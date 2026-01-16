'use strict';

(function(){
	var pickupInput = document.getElementById('pickup_input');
	var dropoffInput = document.getElementById('dropoff_input');
	if(!pickupInput || !dropoffInput) return;

	var pickupLat = document.getElementById('pickup_lat');
	var pickupLng = document.getElementById('pickup_lng');
	var dropLat = document.getElementById('drop_lat');
	var dropLng = document.getElementById('drop_lng');
	var distanceKmField = document.getElementById('distance_km');
	var durationMinField = document.getElementById('duration_min');

	var pickupSuggestions = document.getElementById('pickup_suggestions');
	var dropoffSuggestions = document.getElementById('dropoff_suggestions');

	function debounce(fn, delay){
		var t; return function(){ var ctx=this, args=arguments; clearTimeout(t); t=setTimeout(function(){ fn.apply(ctx,args); }, delay); };
	}

	function geocode(query){
		var url = 'https://nominatim.openstreetmap.org/search?format=json&q=' + encodeURIComponent(query) + '&limit=5';
		return fetch(url, { 
			headers: { 
				'Accept': 'application/json',
				'User-Agent': 'DropMeCabApp/1.0'
			} 
		}).then(function(r){ 
			if(!r.ok) throw new Error('Geocoding request failed');
			return r.json(); 
		});
	}

	function reverseGeocode(lat, lng){
		var url = 'https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=' + encodeURIComponent(lat) + '&lon=' + encodeURIComponent(lng);
		return fetch(url, { headers: { 'Accept': 'application/json' } }).then(function(r){ return r.json(); });
	}

	function renderSuggestions(container, results, onPick){
		container.innerHTML='';
		if(!results || results.length===0){ container.classList.add('hidden'); return; }
		results.slice(0,8).forEach(function(item){
			var div = document.createElement('div');
			div.className='autocomplete-item';
			div.textContent=item.display_name;
			div.addEventListener('click', function(){ onPick(item); container.classList.add('hidden'); });
			container.appendChild(div);
		});
		container.classList.remove('hidden');
	}

	// Store top geocoding result for auto-selection
	var pickupTopResult = null;
	var dropoffTopResult = null;

	var onPickupInput = debounce(function(){
		var q = pickupInput.value.trim();
		if(q.length < 2){ pickupSuggestions.classList.add('hidden'); pickupTopResult = null; return; }
		geocode(q).then(function(results){
			if(results && results.length > 0){
				// Store top result for auto-selection
				pickupTopResult = results[0];
				// Auto-set coordinates from top result if not already set
				if(!pickupLat.value || !pickupLng.value){
					pickupLat.value = pickupTopResult.lat;
					pickupLng.value = pickupTopResult.lon;
					// Update input with full address for better UX
					if(pickupInput.value !== pickupTopResult.display_name){
						pickupInput.value = pickupTopResult.display_name;
					}
					tryRoute();
				}
			}
			renderSuggestions(pickupSuggestions, results, function(item){
				pickupInput.value = item.display_name;
				pickupLat.value = item.lat; pickupLng.value = item.lon;
				pickupTopResult = item; // Update stored result
				tryRoute();
			});
		}).catch(function(err){
			console.error('Geocoding error for pickup:', err);
			pickupTopResult = null;
		});
	}, 300);

	var onDropoffInput = debounce(function(){
		var q = dropoffInput.value.trim();
		if(q.length < 2){ dropoffSuggestions.classList.add('hidden'); dropoffTopResult = null; return; }
		geocode(q).then(function(results){
			if(results && results.length > 0){
				// Store top result for auto-selection
				dropoffTopResult = results[0];
				// Auto-set coordinates from top result if not already set
				if(!dropLat.value || !dropLng.value){
					dropLat.value = dropoffTopResult.lat;
					dropLng.value = dropoffTopResult.lon;
					// Update input with full address for better UX
					if(dropoffInput.value !== dropoffTopResult.display_name){
						dropoffInput.value = dropoffTopResult.display_name;
					}
					tryRoute();
				}
			}
			renderSuggestions(dropoffSuggestions, results, function(item){
				dropoffInput.value = item.display_name;
				dropLat.value = item.lat; dropLng.value = item.lon;
				dropoffTopResult = item; // Update stored result
				tryRoute();
			});
		}).catch(function(err){
			console.error('Geocoding error for dropoff:', err);
			dropoffTopResult = null;
		});
	}, 300);

	pickupInput.addEventListener('input', onPickupInput);
	dropoffInput.addEventListener('input', onDropoffInput);
	document.addEventListener('click', function(e){
		if(!pickupSuggestions.contains(e.target) && e.target!==pickupInput){ pickupSuggestions.classList.add('hidden'); }
		if(!dropoffSuggestions.contains(e.target) && e.target!==dropoffInput){ dropoffSuggestions.classList.add('hidden'); }
	});

	// Global map and routing control for route visualization
	var homeMap = null;
	var routeControl = null;
	var pickupMarker = null;
	var dropoffMarker = null;
	var routePolyline = null;

	// Initialize map on homepage if container exists
	function initHomeMap(){
		var mapContainer = document.getElementById('home-route-map');
		if(!mapContainer || homeMap) return;

		homeMap = L.map('home-route-map', {
			scrollWheelZoom: false,
			zoomControl: false
		});
		L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
			attribution: '&copy; OpenStreetMap contributors'
		}).addTo(homeMap);

		// Set initial view (India center)
		homeMap.setView([20.5937, 78.9629], 5);
		window.__homeLeafletMap = homeMap; // Expose for geolocation
	}

	// Draw route on map
	function drawRouteOnMap(pickupCoords, dropoffCoords){
		// Check if route map container exists (route preview disabled on homepage)
		var mapContainer = document.getElementById('route-map-container');
		if(!mapContainer) return; // Route preview not enabled on this page
		
		if(!homeMap) initHomeMap();
		if(!homeMap) return; // Map container doesn't exist

		// Show map container
		mapContainer.classList.remove('hidden');

		// Clear existing markers and route
		if(pickupMarker) homeMap.removeLayer(pickupMarker);
		if(dropoffMarker) homeMap.removeLayer(dropoffMarker);
		if(routeControl) homeMap.removeControl(routeControl);
		if(routePolyline) homeMap.removeLayer(routePolyline);

		// Ensure coordinates are numbers and in [lat, lng] format
		var pickupLat = parseFloat(pickupCoords[0]);
		var pickupLng = parseFloat(pickupCoords[1]);
		var dropoffLat = parseFloat(dropoffCoords[0]);
		var dropoffLng = parseFloat(dropoffCoords[1]);

		// Validate coordinates
		if(isNaN(pickupLat) || isNaN(pickupLng) || isNaN(dropoffLat) || isNaN(dropoffLng)){
			console.error('Invalid coordinates:', {pickupCoords, dropoffCoords});
			return;
		}

		// Create markers with correct [lat, lng] order
		var pickupLatLng = L.latLng(pickupLat, pickupLng);
		var dropoffLatLng = L.latLng(dropoffLat, dropoffLng);

		// Create custom markers
		var pickupIcon = L.divIcon({
			className: 'custom-pickup-marker',
			html: '<div style="background: #10b981; width: 30px; height: 30px; border-radius: 50% 50% 50% 0; transform: rotate(-45deg); border: 3px solid white; box-shadow: 0 2px 8px rgba(0,0,0,0.3);"><i class="fas fa-map-marker-alt" style="transform: rotate(45deg); color: white; position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%) rotate(45deg);"></i></div>',
			iconSize: [30, 30],
			iconAnchor: [15, 30]
		});

		var dropoffIcon = L.divIcon({
			className: 'custom-dropoff-marker',
			html: '<div style="background: #dc2626; width: 30px; height: 30px; border-radius: 50% 50% 50% 0; transform: rotate(-45deg); border: 3px solid white; box-shadow: 0 2px 8px rgba(0,0,0,0.3);"><i class="fas fa-flag-checkered" style="transform: rotate(45deg); color: white; position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%) rotate(45deg); font-size: 12px;"></i></div>',
			iconSize: [30, 30],
			iconAnchor: [15, 30]
		});

		pickupMarker = L.marker(pickupLatLng, {icon: pickupIcon}).addTo(homeMap);
		pickupMarker.bindPopup('<b>Pickup</b><br>' + (pickupInput.value || 'Pickup Location')).openPopup();

		dropoffMarker = L.marker(dropoffLatLng, {icon: dropoffIcon}).addTo(homeMap);
		dropoffMarker.bindPopup('<b>Dropoff</b><br>' + (dropoffInput.value || 'Dropoff Location'));

		// Create routing control
		routeControl = L.Routing.control({
			waypoints: [pickupLatLng, dropoffLatLng],
			router: L.Routing.osrmv1({
				serviceUrl: 'https://router.project-osrm.org/route/v1'
			}),
			addWaypoints: false,
			draggableWaypoints: false,
			fitSelectedRoutes: true,
			show: false,
			lineOptions: {
				styles: [
					{color: '#00A59E', opacity: 0.8, weight: 6},
					{color: '#0EB9D3', opacity: 0.6, weight: 4}
				]
			}
		}).addTo(homeMap);

		// Handle route found
		routeControl.on('routesfound', function(e){
			var route = e.routes && e.routes[0];
			if(!route) return;

			var meters = route.summary.totalDistance || 0;
			var seconds = route.summary.totalTime || 0;
			var km = (meters / 1000).toFixed(2);
			var minutes = Math.round(seconds / 60);

			// Update hidden fields
			if(distanceKmField) distanceKmField.value = km;
			if(durationMinField) durationMinField.value = minutes.toString();

			// Update distance display if it exists (only on pages with route preview)
			var distanceDisplay = document.getElementById('home-distance-display');
			if(distanceDisplay){
				distanceDisplay.textContent = km + ' km';
				distanceDisplay.classList.remove('hidden');
			}
			// Note: distanceDisplay won't exist on HomepageCab.html (route preview removed)

			// Fit map to route
			var coordinates = route.coordinates || [];
			if(coordinates.length){
				var latLngs = coordinates.map(function(c){
					return L.latLng(c.lat, c.lng);
				});
				var routeBounds = L.latLngBounds(latLngs);
				homeMap.fitBounds(routeBounds.pad(0.2));
			} else {
				var group = new L.FeatureGroup([pickupMarker, dropoffMarker]);
				homeMap.fitBounds(group.getBounds().pad(0.2));
			}

			setTimeout(function(){ homeMap.invalidateSize(); }, 100);
		});

		routeControl.on('routingerror', function(){
			// Fallback: calculate distance using Haversine
			var distance = haversineDistance(pickupLatLng, dropoffLatLng);
			var km = distance.toFixed(2);
			if(distanceKmField) distanceKmField.value = km;
			if(durationMinField) durationMinField.value = Math.round(distance / 0.5).toString(); // Assume 30 km/h

			// Update distance display if it exists (only on pages with route preview)
			var distanceDisplay = document.getElementById('home-distance-display');
			if(distanceDisplay){
				distanceDisplay.textContent = km + ' km (approx)';
				distanceDisplay.classList.remove('hidden');
			}
			// Note: distanceDisplay won't exist on HomepageCab.html (route preview removed)

			// Draw simple polyline as fallback
			routePolyline = L.polyline([pickupLatLng, dropoffLatLng], {
				color: '#00A59E',
				weight: 5,
				opacity: 0.7,
				dashArray: '10, 10'
			}).addTo(homeMap);

			// Fit to markers
			var group = new L.FeatureGroup([pickupMarker, dropoffMarker]);
			homeMap.fitBounds(group.getBounds().pad(0.2));
			setTimeout(function(){ homeMap.invalidateSize(); }, 100);
		});
	}

	// Haversine distance calculation (fallback)
	function haversineDistance(latLng1, latLng2){
		var R = 6371; // Earth radius in km
		var lat1 = latLng1.lat * Math.PI / 180;
		var lat2 = latLng2.lat * Math.PI / 180;
		var dLat = (latLng2.lat - latLng1.lat) * Math.PI / 180;
		var dLng = (latLng2.lng - latLng1.lng) * Math.PI / 180;
		var a = Math.sin(dLat/2) * Math.sin(dLat/2) +
			Math.cos(lat1) * Math.cos(lat2) *
			Math.sin(dLng/2) * Math.sin(dLng/2);
		var c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
		return R * c;
	}

	function tryRoute(){
		if(!pickupLat.value || !pickupLng.value || !dropLat.value || !dropLng.value) return;

		// Ensure coordinates are numbers
		var pickupLatVal = parseFloat(pickupLat.value);
		var pickupLngVal = parseFloat(pickupLng.value);
		var dropLatVal = parseFloat(dropLat.value);
		var dropLngVal = parseFloat(dropLng.value);

		if(isNaN(pickupLatVal) || isNaN(pickupLngVal) || isNaN(dropLatVal) || isNaN(dropLngVal)){
			console.error('Invalid coordinates in tryRoute');
			return;
		}

		// Draw route on homepage map (only if route preview container exists)
		// Route preview is disabled on HomepageCab.html, only enabled on choose_ride.html
		drawRouteOnMap([pickupLatVal, pickupLngVal], [dropLatVal, dropLngVal]);

		// Calculate distance for form submission (using routing API if available, else Haversine)
		// Check if Leaflet Routing Machine is available
		if(typeof L !== 'undefined' && L.Routing && L.Routing.control){
			var p = L.latLng(pickupLatVal, pickupLngVal);
			var d = L.latLng(dropLatVal, dropLngVal);
			
			// Create a temporary routing control just for distance calculation
			var tempControl = L.Routing.control({
				waypoints: [p, d],
				router: L.Routing.osrmv1({ serviceUrl: 'https://router.project-osrm.org/route/v1' }),
				addWaypoints: false,
				draggableWaypoints: false,
				routeWhileDragging: false,
				fitSelectedRoutes: false,
				show: false
			});

			// Use a dummy map for calculation
			var dummyMap = L.map(document.createElement('div'));
			tempControl.addTo(dummyMap);

			tempControl.on('routesfound', function(e){
				var route = e.routes[0];
				var meters = route.summary.totalDistance || 0;
				var seconds = route.summary.totalTime || 0;
				if(distanceKmField) distanceKmField.value = (meters/1000).toFixed(2);
				if(durationMinField) durationMinField.value = Math.round(seconds/60).toString();
				
				// Clean up dummy map
				dummyMap.remove();
			});

			tempControl.on('routingerror', function(){
				// Fallback: use Haversine
				var distance = haversineDistance(p, d);
				if(distanceKmField) distanceKmField.value = distance.toFixed(2);
				if(durationMinField) durationMinField.value = Math.round(distance / 0.5).toString();
				dummyMap.remove();
			});
		} else {
			// If Leaflet Routing Machine not available, use Haversine formula directly
			var p = {lat: pickupLatVal, lng: pickupLngVal};
			var d = {lat: dropLatVal, lng: dropLngVal};
			var distance = haversineDistance(p, d);
			if(distanceKmField) distanceKmField.value = distance.toFixed(2);
			if(durationMinField) durationMinField.value = Math.round(distance / 0.5).toString();
		}
	}

	var form = document.getElementById('rideForm');
	if(form){
		form.addEventListener('submit', function(e){
			e.preventDefault(); // Prevent default submission
			
			var pickupText = pickupInput.value.trim();
			var dropoffText = dropoffInput.value.trim();
			
			// Validate inputs
			if(!pickupText || !dropoffText){
				alert('Please enter both pickup and dropoff locations.');
				return;
			}
			
			// Function to geocode and set coordinates
			function ensureCoordinates(){
				var tasks = [];
				var needsGeocoding = false;
				
				// Check if we need to geocode pickup
				if(!pickupLat.value || !pickupLng.value){
					needsGeocoding = true;
					tasks.push(
						geocode(pickupText).then(function(results){
							if(results && results.length > 0){
								var topResult = results[0];
								pickupLat.value = topResult.lat;
								pickupLng.value = topResult.lon;
								// Update input with full address
								if(pickupInput.value !== topResult.display_name){
									pickupInput.value = topResult.display_name;
								}
								return true;
							}
							throw new Error('No geocoding results for pickup');
						})
					);
				}
				
				// Check if we need to geocode dropoff
				if(!dropLat.value || !dropLng.value){
					needsGeocoding = true;
					tasks.push(
						geocode(dropoffText).then(function(results){
							if(results && results.length > 0){
								var topResult = results[0];
								dropLat.value = topResult.lat;
								dropLng.value = topResult.lon;
								// Update input with full address
								if(dropoffInput.value !== topResult.display_name){
									dropoffInput.value = topResult.display_name;
								}
								return true;
							}
							throw new Error('No geocoding results for dropoff');
						})
					);
				}
				
				// If we need geocoding, wait for it
				if(needsGeocoding && tasks.length > 0){
					return Promise.all(tasks).then(function(){
						// Calculate route after geocoding
						tryRoute();
						return true;
					}).catch(function(err){
						console.error('Geocoding failed:', err);
						alert('Unable to resolve one or both locations. Please select a location from the suggestions or check your input.');
						return false;
					});
				}
				
				// Coordinates already set, just calculate route
				tryRoute();
				return Promise.resolve(true);
			}
			
			// Ensure coordinates are set before submitting
			ensureCoordinates().then(function(success){
				if(success){
					// Verify coordinates are set before submitting
					if(pickupLat.value && pickupLng.value && dropLat.value && dropLng.value){
						// Submit the form
						form.submit();
					} else {
						alert('Please select valid locations from the suggestions or wait for location resolution.');
					}
				}
			});
		});
	}

	// Geolocate button behavior: detect current position, center optional map, set pickup
	var geoBtn = document.getElementById('pickup_geolocate_btn');
	if(geoBtn && navigator.geolocation){
		geoBtn.addEventListener('click', function(){
			var originalClasses = geoBtn.className;
			geoBtn.classList.add('opacity-70');
			var icon = geoBtn.querySelector('i');
			if(icon) icon.classList.add('fa-spin');

			navigator.geolocation.getCurrentPosition(function(pos){
				var lat = pos.coords.latitude;
				var lng = pos.coords.longitude;
				pickupLat.value = lat;
				pickupLng.value = lng;

				reverseGeocode(lat, lng).then(function(data){
					var address = (data && (data.display_name || (data.address && data.address.road))) || 'Current location';
					pickupInput.value = address;
				}).catch(function(){
					pickupInput.value = 'Current location';
				}).finally(function(){
					tryRoute();
				});

				// If a homepage Leaflet map exists globally, center and add/update a marker
				var homeMap = window.__homeLeafletMap;
				if(homeMap && typeof homeMap.setView === 'function'){
					homeMap.setView([lat, lng], 15);
					if(!window.__homeUserMarker){
						window.__homeUserMarker = L.marker([lat, lng]).addTo(homeMap).bindPopup('You are here');
					}else{
						window.__homeUserMarker.setLatLng([lat, lng]);
					}
					window.__homeUserMarker.openPopup();
					setTimeout(function(){ try{ homeMap.invalidateSize(); }catch(e){} }, 100);
				}

				geoBtn.className = originalClasses;
				if(icon) icon.classList.remove('fa-spin');
			}, function(err){
				geoBtn.className = originalClasses;
				if(icon) icon.classList.remove('fa-spin');
				alert('Unable to access your location. Please allow location permissions in your browser.');
			}, { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 });
		});
	}
})();


