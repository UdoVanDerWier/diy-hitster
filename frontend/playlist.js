const API = window._env_.API;
const URL = window._env_.URL;

let playlistTracks = []; // cached tracks

// Extract playlist info from URL
const params = new URLSearchParams(window.location.search);
const playlistId = params.get("id");
const playlistName = params.get("name") || "Playlist";

if (!playlistId) {
    console.error("No playlistId found in URL");
}

async function universalFetch(url, options = {}) {
    console.log("Fetching:", url);
    const response = await fetch(url, { ...options, credentials: "include" });
    return response.json();
}

// Load songs once and display in table
async function loadSongs() {
    if (!playlistId) return;

    const tableBody = document.querySelector("#songsTable tbody");
    tableBody.innerHTML = "Loading...";

    let data = await universalFetch(`${API}/spotify/getPlayLists/${playlistId}`);
    data = data.data.tracks; // only tracks

    playlistTracks = data; // cache globally
    tableBody.innerHTML = "";

    if (!data || !data.items || data.items.length === 0) {
        tableBody.innerHTML = "<tr><td colspan='3'>No songs found.</td></tr>";
        return playlistTracks;
    }

    data.items.forEach(item => {
        const track = item.track;
        const name = track.name;
        const artists = track.artists.map(a => a.name).join(", ");
        const releaseYear = track.album?.release_date?.split("-")[0] || "N/A";

        const row = document.createElement("tr");
        row.innerHTML = `
            <td>${name}</td>
            <td>${artists}</td>
            <td>${releaseYear}</td>
        `;
        tableBody.appendChild(row);
    });

    return playlistTracks;
}

// Optimized QR code to data URL
function generateQrDataUrl(text, size = 60) {
    return new Promise((resolve, reject) => {
        const qrContainer = document.createElement("div");
        const qr = new QRCode(qrContainer, {
            text,
            width: size,
            height: size,
            correctLevel: QRCode.CorrectLevel.H
        });
        setTimeout(() => {
            try {
                const canvas = qrContainer.querySelector("canvas");
                resolve(canvas.toDataURL("image/png"));
            } catch (err) {
                reject(err);
            }
        }, 10);
    });
}

function getRandomVibrantColor() {
    // Generates a value between 0 and 255 (full spectrum)
    const r = Math.floor(Math.random() * 256); 
    const g = Math.floor(Math.random() * 256);
    const b = Math.floor(Math.random() * 256);
    
    return [r, g, b];
}

async function generateHitsterPDF() {
    if (playlistTracks.length === 0) await loadSongs();

    const data = playlistTracks;
    const { jsPDF } = window.jspdf;

    const doc = new jsPDF({ orientation: "portrait", unit: "mm", format: "a4" });
    const pageWidth = 150;
    const pageHeight = 297;

    const cardWidth = 65;   // width of each card
    const cardHeight = 65;  // height of each card
    const marginX = 2.5;
    const marginY = 10;
    const gapX = 2.5;
    const gapY = 5;

    const cardsPerRow = 3;

    // --- Page 1: QR Codes side ---
    let x = gapX, y = marginY;
    for (let i = 0; i < data.items.length; i++) {
        const track = data.items[i].track;
        const spotifyUrl = track.uri;
        // spotifyurl
        const qrDataUrl = await generateQrDataUrl(`${API}/spotify/play/${spotifyUrl}`, Math.min(cardWidth, cardHeight));

        // Pastel background for QR card
        const [r, g, b] = getRandomVibrantColor();
        doc.setFillColor(r, g, b);
        doc.rect(x, y, cardWidth, cardHeight, "F");

        // Border
        doc.setDrawColor(0);
        doc.rect(x, y, cardWidth, cardHeight, "S");

        // Add QR
        doc.addImage(qrDataUrl, "PNG", x + 5, y + 5, cardWidth - 10, cardHeight - 10);

        x += cardWidth + gapX;
        if ((i + 1) % cardsPerRow === 0) {
            x = marginX;
            y += cardHeight + gapY;
        }
        if (y + cardHeight > pageHeight - marginY) {
            doc.addPage();
            x = marginX;
            y = marginY;
        }
    }

    // --- Page 2: Info side ---
    doc.addPage();
    x = gapX;
    y = marginY;

    for (let i = 0; i < data.items.length; i++) {
        const track = data.items[i].track;
        const title = track.name;
        const artists = track.artists.map(a => a.name).join(", ");
        const releaseYear = track.album?.release_date?.split("-")[0] || "N/A";

        // Pastel background
        const [r, g, b] = getRandomVibrantColor();
        doc.setFillColor(r, g, b);
        doc.rect(x, y, cardWidth, cardHeight, "F");

        // Border
        doc.setDrawColor(0);
        doc.rect(x, y, cardWidth, cardHeight, "S");

        const padding = 4;
        let textY = y + padding;

        // Title
        doc.setFont("helvetica", "bold");
        doc.setFontSize(15);
        const titleLines = doc.splitTextToSize(title, cardWidth - padding);
        doc.setTextColor(0);
        doc.text(titleLines, x + (cardWidth / 2), textY + padding, { align: 'center' });
        textY += titleLines.length * 12;
    //
        // Year
        doc.setFontSize(40);
        doc.text(`${releaseYear}`, x + (cardWidth / 4), y + cardHeight / 2);

        // Artists
        doc.setFont("helvetica", "normal");
        doc.setFontSize(10);
        const artistLines = doc.splitTextToSize(artists, cardWidth);
        doc.text(artistLines, x + (cardWidth / 2), y + (cardHeight / 2) + 20, { align: 'center' });
        textY += artistLines.length * 5;



        // Move to next card
        x += cardWidth + (gapX);
        if ((i + 1) % cardsPerRow === 0) {
            x = marginX;
            y += cardHeight + gapY;
        }
        if (y + cardHeight > pageHeight - marginY) {
            doc.addPage();
            x = marginX;
            y = marginY;
        }
    }

    doc.save(`${playlistName}_hitster_style_cards.pdf`);
}


// --- Event listeners ---
document.addEventListener("DOMContentLoaded", async () => {
    document.getElementById("playlistTitle").textContent = playlistName;
    await loadSongs();
    document.getElementById("generatePdfBtn").addEventListener("click", generateHitsterPDF);
});

