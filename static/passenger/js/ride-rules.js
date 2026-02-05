/* Shared ride rules for frontend (single source of truth in JS layer). */
(function(global){
  'use strict';

  var RideRules = {
    normalizeText: function(value){
      return (value || '').toString().trim().toLowerCase();
    },
    normalizeRideType: function(value){
      var v = RideRules.normalizeText(value);
      if(v === 'ride-now' || v === 'ride_now') return 'daily';
      return v;
    },
    parseList: function(value){
      if(!value) return [];
      return value.split(',').map(function(item){ return RideRules.normalizeText(item); }).filter(Boolean);
    },
    extractAddressParts: function(result){
      var address = (result && result.address) ? result.address : {};
      var city = address.city || address.town || address.village || address.hamlet || address.municipality || address.suburb || '';
      var district = address.state_district || address.county || address.district || '';
      var state = address.state || address.province || address.region || '';
      return {
        city: city,
        district: district,
        state: state,
        countryCode: address.country_code || '',
        raw: address
      };
    },
    getPrimaryLocality: function(meta){
      if(!meta) return '';
      return meta.city || meta.district || '';
    },
    isDailyAllowed: function(pickupMeta, dropoffMeta, options){
      if(!pickupMeta || !dropoffMeta) return {allowed: null, reason: 'missing'};

      var pickupCity = RideRules.normalizeText(RideRules.getPrimaryLocality(pickupMeta));
      var dropCity = RideRules.normalizeText(RideRules.getPrimaryLocality(dropoffMeta));
      var pickupState = RideRules.normalizeText(pickupMeta.state);
      var dropState = RideRules.normalizeText(dropoffMeta.state);

      if(!pickupCity || !dropCity || !pickupState || !dropState){
        return {allowed: null, reason: 'incomplete'};
      }

      var sameCity = pickupCity && dropCity && pickupCity === dropCity && pickupState === dropState;
      var allowedCities = RideRules.parseList(options && options.allowedCities);
      var allowedStates = RideRules.parseList(options && options.allowedStates);
      var bothInAllowedCities = allowedCities.length > 0 && allowedCities.indexOf(pickupCity) !== -1 && allowedCities.indexOf(dropCity) !== -1;
      var sameAllowedState = allowedStates.length > 0 && pickupState === dropState && allowedStates.indexOf(pickupState) !== -1;

      return {allowed: sameCity || bothInAllowedCities || sameAllowedState, reason: sameCity ? 'same-city' : 'boundary'};
    },
    shouldSwitchToOutstation: function(currentRideType, distanceKm, thresholdKm){
      var selected = RideRules.normalizeRideType(currentRideType);
      if(selected !== 'daily') return false;
      if(!distanceKm || isNaN(distanceKm)) return false;
      return distanceKm >= thresholdKm;
    },
    isVehicleAllowed: function(rideType, serviceName, disallowedList){
      var type = RideRules.normalizeRideType(rideType);
      if(type !== 'outstation') return true;
      var disallowed = (disallowedList || []).map(function(item){ return RideRules.normalizeText(item); });
      var service = RideRules.normalizeText(serviceName);
      return disallowed.indexOf(service) === -1;
    }
  };

  global.RideRules = RideRules;
})(window);
