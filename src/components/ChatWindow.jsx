import { useState } from "react";
import { motion } from "framer-motion";
import { Upload, MessageCircle, Send, FileText } from "lucide-react";

const ChatWindow = () => {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState("");
    const [loading, setLoading] = useState(false);
    const [language, setLanguage] = useState("en"); // Default response language

    const sendMessage = async () => {
        if (!input.trim()) return;

        const userMessage = { sender: "user", text: input };
        setMessages((prev) => [...prev, userMessage]);
        setInput("");
        setLoading(true);

        try {
            const response = await fetch("http://127.0.0.1:8000/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ query: input, response_language: language }),
            });

            const data = await response.json();
            console.log("Chat API Response:", data);

            if (data.response) {
                const botMessage = { sender: "bot", text: data.response };
                setMessages((prev) => [...prev, botMessage]);
            } else {
                console.error("Invalid response:", data);
            }
        } catch (error) {
            console.error("Error sending message:", error);
        } finally {
            setLoading(false);
        }
    };

    const uploadFile = async (event) => {
        const file = event.target.files[0];
        if (!file) return;

        const formData = new FormData();
        formData.append("file", file);

        try {
            const response = await fetch("http://127.0.0.1:8000/upload_pdf", {
                method: "POST",
                body: formData,
            });

            const data = await response.json();
            console.log("File Upload API Response:", data);

            if (data.file_name) {
                const fileMessage = {
                    sender: "user",
                    file: data.file_name,
                    text: `${data.file_name} uploaded successfully.`,
                };
                setMessages((prev) => [...prev, fileMessage]);
            } else {
                alert("Error uploading file!");
            }
        } catch (error) {
            console.error("File upload error:", error);
            alert("Error uploading file!");
        }
    };

    return (
        <div className="w-full h-full flex flex-col justify-between bg-[#1E1E1E] text-white p-8 rounded-lg shadow-xl">
            {/* Header */}
            <div className="flex items-center justify-center mb-4">
                <MessageCircle className="h-8 w-8 text-[#0FA47F] mr-3" />
                <h1 className="text-2xl font-semibold text-[#0FA47F]">How can I help you today?</h1>
            </div>

            {/* Messages */}
            <div className="flex-grow overflow-y-auto space-y-3 pr-2">
                {messages.length === 0 ? (
                    <p className="text-gray-400 text-center mt-10">Start a conversation...</p>
                ) : (
                    messages.map((msg, index) => (
                        <motion.div
                            key={index}
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.3 }}
                            className={`p-4 my-2 rounded-lg max-w-[85%] text-md shadow-md ${
                                msg.sender === "user"
                                    ? "bg-[#0FA47F] text-white self-end text-right" // User messages aligned right
                                    : "bg-[#292929] text-gray-300 self-start text-left" // Bot messages aligned left
                            }`}
                        >
                            {msg.file ? (
                                <div className="flex items-center gap-2">
                                    <FileText className="text-white" />
                                    <span className="underline cursor-pointer">{msg.file}</span>
                                </div>
                            ) : (
                                msg.text
                            )}
                        </motion.div>
                    ))
                )}
                {loading && <p className="text-gray-400 text-center">Thinking...</p>}
            </div>

            {/* Language Selection */}
            <div className="flex items-center gap-4 mb-4">
                <label className="text-gray-300">Response Language:</label>
                <select
                    value={language}
                    onChange={(e) => setLanguage(e.target.value)}
                    className="p-2 rounded bg-[#292929] text-gray-300"
                >
                    <option value="en">English</option>
                    <option value="ne">Nepali</option>
                </select>
            </div>

            {/* Input & Upload */}
            <div className="flex items-center bg-[#292929] rounded-xl p-3 gap-3 shadow-lg">
                <label
                    htmlFor="fileUpload"
                    className="cursor-pointer bg-[#3A3A3A] text-gray-300 px-4 py-2 rounded-lg hover:bg-[#4A4A4A] transition flex items-center gap-2"
                >
                    <Upload className="text-gray-400" /> Upload File
                    <input type="file" onChange={uploadFile} className="hidden" id="fileUpload" />
                </label>

                <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder="Ask anything..."
                    className="flex-grow p-3 bg-[#1E1E1E] border border-[#0FA47F] rounded-lg focus:ring-2 focus:ring-[#0FA47F] text-gray-300 text-md"
                    onKeyPress={(e) => e.key === "Enter" && sendMessage()}
                />

                <button
                    onClick={sendMessage}
                    className="bg-[#0FA47F] text-white p-3 rounded-lg shadow-lg hover:bg-[#0D8A69] transition text-md flex items-center"
                >
                    <Send className="h-5 w-5" />
                </button>
            </div>
        </div>
    );
};

export default ChatWindow;
