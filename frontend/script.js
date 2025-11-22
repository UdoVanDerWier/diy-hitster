const URL = "http://127.0.0.1:5000";

async function universalFetch(url, options = {}) {
    const response = await fetch(url, { ...options, credentials: "include" });
    return response.json();
}

// Start Spotify login flow
async function startLoginFlow() {
    const data = await universalFetch(
        "http://127.0.0.1:8000/spotify/params?state=" + encodeURIComponent(URL)
    );

    const params = new URLSearchParams(data);
    window.location.href = "https://accounts.spotify.com/authorize?" + params;
}

async function loadPlaylists() {
    const playlistsDiv = document.getElementById("playlists");
    playlistsDiv.innerHTML = "Loading playlists...";

    let data = await universalFetch("http://127.0.0.1:8000/spotify/getPlayLists");
    data = data.data;

    playlistsDiv.innerHTML = "";

    if (!data || !data.items || data.items.length === 0) {
        playlistsDiv.innerHTML = "<p>No playlists found.</p>";
        return;
    }

    data.items.forEach(p => {
        const imgUrl = p.images?.[0]?.url || "https://via.placeholder.com/180?text=No+Image";

        const card = document.createElement("div");
        card.className = "playlist-card";
        card.innerHTML = `
            <img src="${imgUrl}" alt="${p.name}">
            <div class="playlist-info">
                <h3>${p.name}</h3>
                <p>${p.tracks.total} tracks</p>
            </div>
        `;

        // When clicking, go to songs page with playlist ID
        card.addEventListener("click", () => {
            window.location.href = `playlist.html?id=${p.id}&name=${encodeURIComponent(p.name)}`;
        });

        playlistsDiv.appendChild(card);
    });
}


document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("loginBtn").addEventListener("click", startLoginFlow);

    // Try to load playlists automatically if session exists
    loadPlaylists();
});

