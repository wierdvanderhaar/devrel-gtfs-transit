/*
 * L.TileLayer.Grayscale is a regular tilelayer with grayscale makeover.
 * https://github.com/Zverik/leaflet-grayscale/
 */

L.TileLayer.Grayscale = L.TileLayer.extend({
	options: {
		quotaRed: 21,
		quotaGreen: 71,
		quotaBlue: 8,
		quotaDividerTune: 0,
		quotaDivider: function() {
			return this.quotaRed + this.quotaGreen + this.quotaBlue + this.quotaDividerTune;
		}
	},

	initialize: function (url, options) {
		options = options || {}
		options.crossOrigin = true;
		L.TileLayer.prototype.initialize.call(this, url, options);

		this.on('tileload', function(e) {
			this._makeGrayscale(e.tile);
		});
	},

	_createTile: function () {
		var tile = L.TileLayer.prototype._createTile.call(this);
		tile.crossOrigin = "Anonymous";
		return tile;
	},

	_makeGrayscale: function (img) {
		if (img.getAttribute('data-grayscaled'))
			return;

    img.crossOrigin = '';
		var canvas = document.createElement("canvas");
		canvas.width = img.width;
		canvas.height = img.height;
		var ctx = canvas.getContext("2d");
		ctx.drawImage(img, 0, 0);

		var imgd = ctx.getImageData(0, 0, canvas.width, canvas.height);
		var pix = imgd.data;
		for (var i = 0, n = pix.length; i < n; i += 4) {
      pix[i] = pix[i + 1] = pix[i + 2] = (this.options.quotaRed * pix[i] + this.options.quotaGreen * pix[i + 1] + this.options.quotaBlue * pix[i + 2]) / this.options.quotaDivider();
		}
		ctx.putImageData(imgd, 0, 0);
		img.setAttribute('data-grayscaled', true);
		img.src = canvas.toDataURL();
	}
});

L.tileLayer.grayscale = function (url, options) {
	return new L.TileLayer.Grayscale(url, options);
};

/* ---- End Grayscale code ---- */

const myMap = L.map('mapId');
const stopMarkers = L.layerGroup();
const vehicleMarkers = L.layerGroup();

myMap.addLayer(stopMarkers);
myMap.addLayer(vehicleMarkers);

let config;
let routeInfo;
let interval;

async function getConfiguration() {
  const response = await fetch('/api/config');
  const responseObj = await response.json();

  return responseObj.results[0];
}

async function getSystemInfo() {
  const response = await fetch('/api/routeinfo');
  const responseObj = await response.json();

  return responseObj.results;
}

async function drawRouteMap() {
  const response = await fetch('/api/networkmap');
  const routeMap = await response.json();

  L.geoJSON(routeMap.results[0], {
    style: {
      color: '#000000',
      weight: 1
    },
    pointToLayer: function (feature, latlng) {
      const stopMarker = L.circleMarker(latlng, {
        radius: 7,
        fillColor: '#0000000',
        opacity: 0.5,
        fillOpacity: 0.5
      });

      stopMarkers.addLayer(stopMarker);
      return stopMarker;
    },
    onEachFeature: function (feature, layer) {
      if (feature.properties && feature.properties.stop_id) {
        layer.bindPopup(`<h2>${feature.properties.stop_name}</h2><p>ID: ${feature.properties.stop_id}</p>`);
      }
    }
  }).addTo(myMap);
}

async function updateVehicleLocations() {
  const response = await fetch('/api/vehiclepositions');
  const responseDoc = await response.json();

  function getMarkerColor(line) {
    const r = routeInfo.filter(r => r.id === line);
    return (r.length === 1 ? r[0].color : '#000000');
  }

  vehicles = responseDoc.results;

  vehicleMarkers.clearLayers();

  for (const vehicle of vehicles) {
    const markerColor = getMarkerColor(vehicle.line);
  
    const vehicleMarker = L.circleMarker([vehicle.longitude, vehicle.latitude], {
      radius: 5,
      color: markerColor,
      fillColor: markerColor,
      fillOpacity: 1,
      vehicle: {
        tripId: vehicle.tripId,
        vehicleId: vehicle.vehicleId,
        line: vehicle.line,
        licensePlate: vehicle.licensePlate,
        currentStopSequence: vehicle.currentStopSequence
      }
    });

    vehicleMarker.on('click', async function(e) {

      this.setPopupContent(`
        <h2>Loading data...</h2>
      `);

      const upcomingStopsResponse = await fetch(`/api/upcomingstops/${this.options.vehicle.tripId}/${this.options.vehicle.currentStopSequence}/${config.upcomingStopsToShow}`);
      const upcomingStopsResults = await upcomingStopsResponse.json();

      let popupContent = `<h2>${this.options.vehicle.line} ${this.options.vehicle.tripId}</h2><h3>Next Stops:</h3><ol>`;
      for (const upcomingStop of upcomingStopsResults.results) {
        // TODO add times to the popup too...
        popupContent = `${popupContent}<li>${upcomingStop.stopId}</li>`
      }

      popupContent = `${popupContent}</ol>`;
      this.setPopupContent(popupContent);
    });

    vehicleMarker.bindPopup('');
    vehicleMarkers.addLayer(vehicleMarker);
  }
}

(async () => {
  config = await getConfiguration();

  myMap.setView([config.initialLatitude, config.initialLongitude], config.initialZoom);

  L.tileLayer.grayscale(
    'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', 
    {
      maxZoom: config.maxZoom,
      opacity: 0.5,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }
  ).addTo(myMap);
  
  myMap.setMaxBounds(myMap.getBounds());
  myMap.setMinZoom(config.initialZoom);
  
  routeInfo = await getSystemInfo();
  await drawRouteMap();
  updateVehicleLocations();

  interval = setInterval(updateVehicleLocations, 1000);

  document.getElementById('autoRefresh').addEventListener('change', e => {
    if (e.currentTarget.checked) {
      interval = setInterval(updateVehicleLocations, 1000);
    } else {
      clearInterval(interval);
    }
  });

  document.getElementById('showStops').addEventListener('change', e => {
    if (e.currentTarget.checked) {
      myMap.addLayer(stopMarkers);
    } else {
      myMap.removeLayer(stopMarkers);
    }
  });
})();