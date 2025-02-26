import { Upload } from "lucide-react";
const FileUploader = ({ handleFileUpload }) => {
    return (
        <label htmlFor="fileUpload" className="cursor-pointer p-3 bg-[#292929] rounded-lg flex items-center gap-2 hover:bg-[#3A3A3A] transition text-gray-300 shadow-md">
            <Upload className="text-gray-400" /> Upload File
            <input type="file" onChange={handleFileUpload} className="hidden" id="fileUpload" />
        </label>
    );
};
export default FileUploader;
