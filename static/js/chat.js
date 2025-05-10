// Wait until the page fully loads
// document.addEventListener("DOMContentLoaded", function () {
// 	const chatBox = document.getElementById("chat-box");

// 	// Setup SSE to receive new messages
// 	const eventSource = new EventSource("/chat/stream/");

// 	eventSource.onmessage = function (event) {
// 			const [sender, content] = event.data.split(":");
// 			const bubble = document.createElement("div");

// 			if (sender === "patient") {
// 					bubble.className = "chat-bubble chat-bubble-primary mb-2";
// 			} else if (sender === "bot") {
// 					bubble.className = "chat-bubble chat-bubble-accent mb-2";
// 			} else {
// 					bubble.className = "chat-bubble chat-bubble-info mb-2";
// 			}

// 			bubble.textContent = content;
// 			chatBox.appendChild(bubble);

// 			// Auto-scroll after receiving new message from SSE
// 			scrollChatBox();
// 	};
// });

// Global helper function to scroll chatbox smoothly
function scrollChatBox() {
	const chatBox = document.getElementById("chat-box");

	if (chatBox) {
			setTimeout(() => {
					chatBox.scrollTo({
							top: chatBox.scrollHeight,
							behavior: "smooth",
					});
			}, 50); // slight delay so DOM fully updates before scroll
	}
}

function scrollChatBox2() {
	const chatBox = document.getElementById("chat-box");

	if (chatBox && chatBox.lastElementChild) {
		setTimeout(() => {
			chatBox.lastElementChild.scrollIntoView({
				behavior: "smooth",
				block: "start", // or "center" or "end" based on your layout
			});
		}, 50);
	}
}



// Initial scroll on page load
document.addEventListener("DOMContentLoaded", scrollChatBox);

// Re-scroll every time HTMX swaps in new content
document.body.addEventListener("htmx:afterSwap", (e) => {
  if (e.detail.target.id === "chat-box" || e.detail.target.closest("#chat-box")) {
    scrollChatBox();
  }
});