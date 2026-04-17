import { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileText } from 'lucide-react';
import { motion } from 'framer-motion';

export default function DragDropZone({ onFilesAccepted, disabled }) {
  const onDrop = useCallback((acceptedFiles) => {
    if (acceptedFiles?.length > 0 && !disabled) {
      onFilesAccepted(acceptedFiles);
    }
  }, [onFilesAccepted, disabled]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/plain': ['.txt', '.md', '.markdown'],
    },
    disabled
  });

  return (
    <div
      {...getRootProps()}
      className={`
        relative group cursor-pointer overflow-hidden
        p-12 md:p-24 transition-all duration-500 ease-out
        ${disabled ? 'opacity-50 pointer-events-none' : ''}
      `}
    >
      {/* Background with animated dashed border using SVG for exact precision */}
      <svg className="absolute inset-0 w-full h-full pointer-events-none" xmlns="http://www.w3.org/2000/svg">
        <rect 
          x="2" y="2" 
          width="calc(100% - 4px)" height="calc(100% - 4px)" 
          fill="transparent" 
          stroke={isDragActive ? '#E53935' : '#27272a'} 
          strokeWidth="2" 
          strokeDasharray="8 8" 
          className="transition-colors duration-500 ease-out"
        />
      </svg>
      
      {/* Hover overlay */}
      <div className={`
        absolute inset-0 bg-zinc-900/40 transition-opacity duration-500 
        ${isDragActive ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'}
      `} />

      <div className="relative z-10 flex flex-col items-center justify-center text-center">
        <input {...getInputProps()} />
        
        <motion.div
          animate={{ scale: isDragActive ? 1.05 : 1 }}
          transition={{ duration: 0.4, ease: "easeOut" }}
          className="mb-8 p-4 bg-zinc-900 border border-zinc-800 rounded-none shadow-2xl"
        >
          {isDragActive ? (
            <Upload className="w-8 h-8 text-vermillion" strokeWidth={1} />
          ) : (
            <FileText className="w-8 h-8 text-zinc-400 group-hover:text-ivory transition-colors duration-500" strokeWidth={1} />
          )}
        </motion.div>

        <h3 className="font-serif text-xl md:text-2xl text-ivory mb-3">
          {isDragActive ? "Drop artifacts to process" : "Initialize Cognitive Processing"}
        </h3>
        
        <p className="font-mono text-xs uppercase tracking-widest text-zinc-500 max-w-sm">
          Drag & drop .txt or .md files, or click to open system dialogue.
        </p>
      </div>
    </div>
  );
}
