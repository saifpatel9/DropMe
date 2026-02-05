'use strict';

(function(){
	var pickupInput = document.getElementById('pickup_input');
	var dropoffInput = document.getElementById('dropoff_input');
	if(!pickupInput || !dropoffInput) return;

	var pickupLat = document.getElementById('pickup_lat');
	var pickupLng = document.getElementById('pickup_lng');
	var dropLat = document.getElementById('drop_lat');
	var dropLng = document.getElementById('drop_lng');
	var pickupCity = document.getElementById('pickup_city');
	var pickupDistrict = document.getElementById('pickup_district');
	var pickupState = document.getElementById('pickup_state');
	var dropCity = document.getElementById('drop_city');
	var dropDistrict = document.getElementById('drop_district');
	var dropState = document.getElementById('drop_state');
	var distanceKmField = document.getElementById('distance_km');
	var durationMinField = document.getElementById('duration_min');
	var rideTypeInput = document.getElementById('rideTypeInput');
	var rideTypeNotice = document.getElementById('ride_type_notice');
	var rideForm = document.getElementById('rideForm');
	var outstationThresholdKm = rideForm && rideForm.dataset.outstationKm ? parseFloat(rideForm.dataset.outstationKm) : 40;
	var rideRules = window.RideRules || null;

	var pickupSuggestions = document.getElementById('pickup_suggestions');
	var dropoffSuggestions = document.getElementById('dropoff_suggestions');

	function debounce(fn, delay){
		var t; return function(){ var ctx=this, args=arguments; clearTimeout(t); t=setTimeout(function(){ fn.apply(ctx,args); }, delay); };
	}

	function geocode(query){
		var url = 'https://nominatim.openstreetmap.org/search?format=json&addressdetails=1&q=' + encodeURIComponent(query) + '&limit=5';
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
		var url = 'https://nominatim.openstreetmap.org/reverse?format=jsonv2&addressdetails=1&lat=' + encodeURIComponent(lat) + '&lon=' + encodeURIComponent(lng);
		return fetch(url, { headers: { 'Accept': 'application/json' } }).then(function(r){ return r.json(); });
	}

	function extractAddressParts(result){
		if(rideRules && rideRules.extractAddressParts){
			return rideRules.extractAddressParts(result);
		}
		return { city: '', district: '', state: '', countryCode: '', raw: {} };
	}

	function setLocationFields(prefix, meta){
		if(!meta) return;
		if(prefix === 'pickup'){
			if(pickupCity) pickupCity.value = meta.city || '';
			if(pickupDistrict) pickupDistrict.value = meta.district || '';
			if(pickupState) pickupState.value = meta.state || '';
		}else if(prefix === 'dropoff'){
			if(dropCity) dropCity.value = meta.city || '';
			if(dropDistrict) dropDistrict.value = meta.district || '';
			if(dropState) dropState.value = meta.state || '';
		}
	}

	function getStoredMeta(prefix){
		if(prefix === 'pickup'){
			return {
				city: pickupCity ? pickupCity.value : '',
				district: pickupDistrict ? pickupDistrict.value : '',
				state: pickupState ? pickupState.value : ''
			};
		}
		return {
			city: dropCity ? dropCity.value : '',
			district: dropDistrict ? dropDistrict.value : '',
			state: dropState ? dropState.value : ''
		};
	}

	function setNotice(message, tone){
		if(!rideTypeNotice) return;
		if(!message){
			rideTypeNotice.textContent = '';
			rideTypeNotice.classList.add('hidden');
			return;
		}
		rideTypeNotice.textContent = message;
		rideTypeNotice.classList.remove('hidden');
		rideTypeNotice.classList.remove('text-amber-800','bg-amber-50','border-amber-200','text-red-800','bg-red-50','border-red-200','text-green-800','bg-green-50','border-green-200');
		if(tone === 'error'){
			rideTypeNotice.classList.add('text-red-800','bg-red-50','border-red-200');
		}else if(tone === 'success'){
			rideTypeNotice.classList.add('text-green-800','bg-green-50','border-green-200');
		}else{
			rideTypeNotice.classList.add('text-amber-800','bg-amber-50','border-amber-200');
		}
	}

	function normalizeRideType(value){
		return rideRules && rideRules.normalizeRideType ? rideRules.normalizeRideType(value) : (value || '').toString().trim().toLowerCase();
	}

	function switchRideType(targetType){
		var target = normalizeRideType(targetType);
		if(!target) return;
		var tabs = document.querySelectorAll('.booking-tab');
		var matched = null;
		tabs.forEach(function(tab){
			var tabType = normalizeRideType(tab.dataset.tab);
			if(tabType === target) matched = tab;
		});
		if(matched){
			matched.click();
		}else if(rideTypeInput){
			rideTypeInput.value = target;
		}
	}

	function isDailyAllowed(pickupMeta, dropoffMeta){
		if(!rideRules || !rideRules.isDailyAllowed) return {allowed: null, reason: 'missing'};
		return rideRules.isDailyAllowed(pickupMeta, dropoffMeta, {
			allowedCities: rideForm ? rideForm.dataset.dailyCities : '',
			allowedStates: rideForm ? rideForm.dataset.dailyStates : ''
		});
	}

	function validateRideType(){
		var selected = normalizeRideType(rideTypeInput ? rideTypeInput.value : '');
		if(selected !== 'daily') return;

		var pickupMeta = getStoredMeta('pickup');
		var dropoffMeta = getStoredMeta('dropoff');
		var result = isDailyAllowed(pickupMeta, dropoffMeta);

		if(result.allowed === null){
			setNotice('We could not confirm the pickup and dropoff city/state. Please select a suggestion or use current location to validate Daily Ride.', 'info');
			return;
		}

		if(!result.allowed){
			var pickupLabel = (pickupMeta.city || pickupMeta.district || '').trim();
			var dropLabel = (dropoffMeta.city || dropoffMeta.district || '').trim();
			setNotice('Daily Ride is only available within the same city or service area. Pickup: ' + (pickupLabel || 'Unknown') + ', Dropoff: ' + (dropLabel || 'Unknown') + '. Switched to Outstation.', 'error');
			switchRideType('outstation');
			return;
		}

		setNotice('', 'success');
	}

	function applyDistanceRule(distanceKm){
		if(!distanceKm || isNaN(distanceKm)) return;
		var selected = normalizeRideType(rideTypeInput ? rideTypeInput.value : '');
		if(!rideRules || !rideRules.shouldSwitchToOutstation){
			if(selected === 'daily' && distanceKm >= outstationThresholdKm){
				setNotice('Daily Ride is only available within the local service area. This trip is ' + distanceKm.toFixed(1) + ' km, so it was switched to Outstation.', 'error');
				switchRideType('outstation');
			}
			return;
		}
		if(rideRules.shouldSwitchToOutstation(selected, distanceKm, outstationThresholdKm)){
			setNotice('Daily Ride is only available within the local service area. This trip is ' + distanceKm.toFixed(1) + ' km, so it was switched to Outstation.', 'error');
			switchRideType('outstation');
		}
	}

	function safeValidateRideType(){
		try{
			validateRideType();
		}catch(err){
			console.error('Ride type validation failed:', err);
		}
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
			pickupTopResult = results && results.length ? results[0] : null;
			renderSuggestions(pickupSuggestions, results, function(item){
				pickupInput.value = item.display_name;
				pickupLat.value = item.lat; pickupLng.value = item.lon;
				pickupTopResult = item; // Update stored result
				setLocationFields('pickup', extractAddressParts(item));
				tryRoute();
				safeValidateRideType();
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
			dropoffTopResult = results && results.length ? results[0] : null;
			renderSuggestions(dropoffSuggestions, results, function(item){
				dropoffInput.value = item.display_name;
				dropLat.value = item.lat; dropLng.value = item.lon;
				dropoffTopResult = item; // Update stored result
				setLocationFields('dropoff', extractAddressParts(item));
				tryRoute();
				safeValidateRideType();
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
			applyDistanceRule(parseFloat(km));

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
			if(distanceKmField) distanceKmField.value = '';
			if(durationMinField) durationMinField.value = '';
			setNotice('Unable to calculate route distance. Please select suggested locations and try again.', 'error');
			// Keep markers visible even if routing fails
			var group = new L.FeatureGroup([pickupMarker, dropoffMarker]);
			homeMap.fitBounds(group.getBounds().pad(0.2));
			setTimeout(function(){ homeMap.invalidateSize(); }, 100);
		});
	}

	function computeRouteDistance(pickupLatVal, pickupLngVal, dropLatVal, dropLngVal){
		return new Promise(function(resolve){
			if(typeof L === 'undefined' || !L.Routing || !L.Routing.control){
				if(distanceKmField) distanceKmField.value = '';
				if(durationMinField) durationMinField.value = '';
				setNotice('Routing engine unavailable. Please try again later or select suggested locations.', 'error');
				return resolve(false);
			}

			var p = L.latLng(pickupLatVal, pickupLngVal);
			var d = L.latLng(dropLatVal, dropLngVal);
			var tempControl = L.Routing.control({
				waypoints: [p, d],
				router: L.Routing.osrmv1({ serviceUrl: 'https://router.project-osrm.org/route/v1' }),
				addWaypoints: false,
				draggableWaypoints: false,
				routeWhileDragging: false,
				fitSelectedRoutes: false,
				show: false
			});

			var dummyMap = L.map(document.createElement('div'));
			tempControl.addTo(dummyMap);

			tempControl.on('routesfound', function(e){
				var route = e.routes && e.routes[0];
				if(!route){
					if(distanceKmField) distanceKmField.value = '';
					if(durationMinField) durationMinField.value = '';
					setNotice('Unable to calculate route distance. Please select suggested locations and try again.', 'error');
					dummyMap.remove();
					return resolve(false);
				}
				var meters = route.summary.totalDistance || 0;
				var seconds = route.summary.totalTime || 0;
				var kmValue = (meters/1000).toFixed(2);
				if(distanceKmField) distanceKmField.value = kmValue;
				if(durationMinField) durationMinField.value = Math.round(seconds/60).toString();
				applyDistanceRule(parseFloat(kmValue));
				dummyMap.remove();
				return resolve(true);
			});

			tempControl.on('routingerror', function(){
				if(distanceKmField) distanceKmField.value = '';
				if(durationMinField) durationMinField.value = '';
				setNotice('Unable to calculate route distance. Please select suggested locations and try again.', 'error');
				dummyMap.remove();
				return resolve(false);
			});
		});
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

		return computeRouteDistance(pickupLatVal, pickupLngVal, dropLatVal, dropLngVal);
	}

	if(rideForm){
		rideForm.addEventListener('submit', function(e){
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
								setLocationFields('pickup', extractAddressParts(topResult));
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
								setLocationFields('dropoff', extractAddressParts(topResult));
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
						safeValidateRideType();
						return true;
					}).catch(function(err){
						console.error('Geocoding failed:', err);
						alert('Unable to resolve one or both locations. Please select a location from the suggestions or check your input.');
						return false;
					});
				}
				
				// Coordinates already set, just calculate route
				tryRoute();
				safeValidateRideType();
				return Promise.resolve(true);
			}
			
			// Ensure coordinates are set before submitting
			ensureCoordinates().then(function(success){
				if(!success) return;

				var decision = isDailyAllowed(getStoredMeta('pickup'), getStoredMeta('dropoff'));
				if(normalizeRideType(rideTypeInput ? rideTypeInput.value : '') === 'daily' && decision.allowed === false){
					alert('Daily Ride is not available for different cities/states. Please choose Outstation or Intercity.');
					return;
				}

				var routePromise = Promise.resolve(true);
				if(!distanceKmField.value || !durationMinField.value){
					routePromise = tryRoute() || Promise.resolve(false);
				}

				routePromise.then(function(ok){
					if(!ok || !distanceKmField.value || !durationMinField.value){
						setNotice('Unable to calculate route distance. Please select suggested locations and try again.', 'error');
						return;
					}
					// Verify coordinates are set before submitting
					if(pickupLat.value && pickupLng.value && dropLat.value && dropLng.value){
						var params = new URLSearchParams(new FormData(rideForm)).toString();
						var action = rideForm.getAttribute('action') || window.location.pathname;
						window.location.href = action + (params ? ('?' + params) : '');
					} else {
						alert('Please select valid locations from the suggestions or wait for location resolution.');
					}
				});
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
					setLocationFields('pickup', extractAddressParts(data));
				}).catch(function(){
					pickupInput.value = 'Current location';
				}).finally(function(){
					tryRoute();
					safeValidateRideType();
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
