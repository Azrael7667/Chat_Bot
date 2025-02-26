const MessageBubble = ({ sender, text }) => {
    return (
        <div className={`p-3 my-2 rounded-lg max-w-xs ${sender === "user" ? "bg-blue-500 text-white self-end ml-auto" : "bg-gray-300 text-black"}`}>{text}</div>
    );
};
export default MessageBubble;