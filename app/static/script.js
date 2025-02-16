let map;
let userMarker;
let markers = [];

// Haritayı başlat
function initMap() {
  map = L.map("map").setView([40.98566, 29.027361], 13);

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "&copy; OpenStreetMap Katkıda Bulunanlar",
  }).addTo(map);

  userMarker = L.marker([40.98566, 29.027361], { draggable: true })
    .addTo(map)
    .bindPopup("Başlangıç Konumu")
    .openPopup();

  userMarker.on("dragend", function (e) {
    const pos = userMarker.getLatLng();
    document.getElementById("latitude").value = pos.lat.toFixed(6);
    document.getElementById("longitude").value = pos.lng.toFixed(6);
  });
}

// Çap seçildiğinde
function selectRadius(radius) {
  document.getElementById("radius").value = radius;
}

// Kategori seçildiğinde
function selectCategory(tag) {
  document.getElementById("tag").value = tag;
  document
    .querySelectorAll(".chip")
    .forEach((el) => el.classList.remove("selected"));
  event.target.classList.add("selected");
}

// Mekanları ara ve haritada göster
async function search() {
  const latitude = document.getElementById("latitude").value;
  const longitude = document.getElementById("longitude").value;
  const radius = document.getElementById("radius").value;
  const tag = document.getElementById("tag").value;

  console.log("Arama başladı...");

  // Yükleniyor göstergesini aç
  document.getElementById("loading").style.display = "block";

  const response = await fetch("/search", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ latitude, longitude, radius, tag }),
  });

  const data = await response.json();
  const resultsList = document.getElementById("results");
  resultsList.innerHTML = "";

  // Eski markerları temizle
  markers.forEach((marker) => map.removeLayer(marker));
  markers = [];

  if (data.length === 0) {
    resultsList.innerHTML = "<li>Sonuç bulunamadı.</li>";
  } else {
    data.forEach((poi) => {
      const li = document.createElement("li");
      li.textContent = `${poi.name} - Mesafe: ${poi.route_distance_m.toFixed(
        2
      )} m`;
      resultsList.appendChild(li);

      // Mekanı haritada işaretle
      const marker = L.marker([
        poi.coordinates.latitude,
        poi.coordinates.longitude,
      ])
        .addTo(map)
        .bindPopup(
          `<b>${poi.name}</b><br>Mesafe: ${poi.route_distance_m.toFixed(2)} m`
        );
      markers.push(marker);
    });

    map.setView(
      [data[0].coordinates.latitude, data[0].coordinates.longitude],
      14
    );
  }

  console.log("Arama tamamlandı.");

  // Yükleniyor göstergesini kapat
  document.getElementById("loading").style.display = "none";
}

// Sayfa yüklendiğinde haritayı başlat
window.onload = initMap;
