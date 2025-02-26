export const Button = ({ onClick, children }) => {
    return (
        <button onClick={onClick} className="bg-[#0FA47F] text-white p-4 rounded-lg shadow-lg hover:bg-[#0D8A69] transition text-md">
            {children}
        </button>
    );
};
