import { useState } from "react";
import ChatWindow from "../components/ChatWindow";
import Sidebar from "../components/Sidebar";
const Home = () => {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState("");
    const [file, setFile] = useState(null);
    const handleSend = () => {
        if (input.trim() === "") return;
        setMessages([...messages, { sender: "user", text: input }]);
        setInput("");
        setTimeout(() => {
            setMessages([...messages, { sender: "bot", text: "Processing file and response..." }]);
        }, 1000);
    };
    const handleFileUpload = (event) => {
        setFile(event.target.files[0]);
    };
    return (
        <div className="flex h-screen bg-[#101010] text-white">
            <Sidebar />
            <div className="w-5/6 flex flex-col">
                <ChatWindow messages={messages} input={input} setInput={setInput} handleSend={handleSend} handleFileUpload={handleFileUpload} />
            </div>
        </div>
    );
};
export default Home;
