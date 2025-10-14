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
		var url = 'https://nominatim.openstreetmap.org/search?format=json&q=' + encodeURIComponent(query);
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

	var onPickupInput = debounce(function(){
		var q = pickupInput.value.trim();
		if(q.length < 2){ pickupSuggestions.classList.add('hidden'); return; }
		geocode(q).then(function(results){
			renderSuggestions(pickupSuggestions, results, function(item){
				pickupInput.value = item.display_name;
				pickupLat.value = item.lat; pickupLng.value = item.lon;
				tryRoute();
			});
		});
	}, 300);

	var onDropoffInput = debounce(function(){
		var q = dropoffInput.value.trim();
		if(q.length < 2){ dropoffSuggestions.classList.add('hidden'); return; }
		geocode(q).then(function(results){
			renderSuggestions(dropoffSuggestions, results, function(item){
				dropoffInput.value = item.display_name;
				dropLat.value = item.lat; dropLng.value = item.lon;
				tryRoute();
			});
		});
	}, 300);

	pickupInput.addEventListener('input', onPickupInput);
	dropoffInput.addEventListener('input', onDropoffInput);
	document.addEventListener('click', function(e){
		if(!pickupSuggestions.contains(e.target) && e.target!==pickupInput){ pickupSuggestions.classList.add('hidden'); }
		if(!dropoffSuggestions.contains(e.target) && e.target!==dropoffInput){ dropoffSuggestions.classList.add('hidden'); }
	});

	function tryRoute(){
		if(!pickupLat.value || !pickupLng.value || !dropLat.value || !dropLng.value) return;
		var p = L.latLng(parseFloat(pickupLat.value), parseFloat(pickupLng.value));
		var d = L.latLng(parseFloat(dropLat.value), parseFloat(dropLng.value));
		L.Routing.control({ waypoints:[p,d], addWaypoints:false, draggableWaypoints:false, routeWhileDragging:false, fitSelectedRoutes:false, show:false }).on('routesfound', function(e){
			var route = e.routes[0];
			var meters = route.summary.totalDistance || 0;
			var seconds = route.summary.totalTime || 0;
			distanceKmField.value = (meters/1000).toFixed(2);
			durationMinField.value = Math.round(seconds/60).toString();
		}).on('routingerror', function(){ /* ignore */ }).addTo(L.map(document.createElement('div')));
	}

	var form = document.getElementById('rideForm');
	if(form){
		form.addEventListener('submit', function(){
			// if user didn't pick from suggestions, try geocode once
			var tasks = [];
			if(!pickupLat.value || !pickupLng.value){
				tasks.push(geocode(pickupInput.value).then(function(r){ if(r[0]){ pickupLat.value=r[0].lat; pickupLng.value=r[0].lon; } }));
			}
			if(!dropLat.value || !dropLng.value){
				tasks.push(geocode(dropoffInput.value).then(function(r){ if(r[0]){ dropLat.value=r[0].lat; dropLng.value=r[0].lon; } }));
			}
			if(tasks.length){
				Promise.all(tasks).then(function(){ tryRoute(); });
			}
		});
	}
})();


