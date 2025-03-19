let isLoading = false;

function addToHistory(message) {
    const historyList = document.getElementById('historyList');
    const historyItem = document.createElement('div');
    historyItem.classList.add('history-item');
    historyItem.textContent = message.length > 30 ? message.substring(0, 30) + '...' : message;
    historyItem.title = message;
    historyItem.onclick = () => {
        document.getElementById('userInput').value = message;
    };
    historyList.appendChild(historyItem);
}

function showLoading() {
    const chatBox = document.getElementById("messages");
    const loadingDiv = document.createElement("div");
    loadingDiv.classList.add("message", "bot", "loading");
    loadingDiv.innerHTML = `
        <img src="https://via.placeholder.com/30" alt="Bot Icon">
        <div class="loading-dots">
            <div class="dot"></div>
            <div class="dot"></div>
            <div class="dot"></div>
        </div>
    `;
    loadingDiv.id = "loadingMessage";
    chatBox.appendChild(loadingDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
}

function removeLoading() {
    const loadingMessage = document.getElementById("loadingMessage");
    if (loadingMessage) {
        loadingMessage.remove();
    }
}

async function sendMessage() {
    if (isLoading) return;
    
    let input = document.getElementById("userInput");
    let message = input.value.trim();
    if (!message) return;
    
    isLoading = true;
    let chatBox = document.getElementById("messages");
    
    // Add to history
    addToHistory(message);
    
    // Show user message
    let userMessage = document.createElement("div");
    userMessage.classList.add("message", "user");
    userMessage.textContent = message;
    chatBox.appendChild(userMessage);
    
    input.value = "";
    chatBox.scrollTop = chatBox.scrollHeight;
    
    showLoading();
    
    try {
        let response = await fetch("http://localhost:8000/query", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
                prompt: message,
                latitude: 41.064108,
                longitude: 29.031473,
                radius: 2000,
                num_results: 5
            })
        });
        
        removeLoading();
        
        if (!response.ok) throw new Error("API request failed");
        
        let data = await response.json();
        let locationAdvice = data.location_advice || "No location advice available.";
        
        let botMessage = document.createElement("div");
        botMessage.classList.add("message", "bot");
        botMessage.textContent = locationAdvice;
        chatBox.appendChild(botMessage);
        
        chatBox.scrollTop = chatBox.scrollHeight;
    } catch (error) {
        removeLoading();
        let botMessage = document.createElement("div");
        botMessage.classList.add("message", "bot");
        botMessage.textContent = `Error: ${error.message}`;
        chatBox.appendChild(botMessage);
        chatBox.scrollTop = chatBox.scrollHeight;
    }
    
    isLoading = false;
}

// Event Listeners
document.getElementById("userInput").addEventListener("keypress", (e) => {
    if (e.key === "Enter") {
        sendMessage();
    }
});

// Focus input on load
window.addEventListener('load', () => {
    document.getElementById("userInput").focus();
    
    // Auto-collapse on mobile
    if (window.innerWidth <= 768) {
        historyPanel.classList.add('collapsed');
    }
});

// Handle window resize
window.addEventListener('resize', () => {
    if (window.innerWidth <= 768) {
        historyPanel.classList.add('collapsed');
    } else {
        historyPanel.classList.remove('collapsed');
    }
});

const toggleHistoryBtn = document.getElementById('toggleHistory');
const historyPanel = document.getElementById('historyPanel');

toggleHistoryBtn.addEventListener('click', () => {
    historyPanel.classList.toggle('collapsed');
});