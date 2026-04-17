import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { motion } from 'framer-motion';

export default function RoadmapDocument({ content }) {
  if (!content) return null;

  return (
    <motion.article
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
      style={{
        backgroundColor: '#09090b',
        border: '1px solid #27272a',
        padding: '4rem 4.5rem',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {/* Decorative corner lines */}
      <div style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '2px', background: 'linear-gradient(to right, #E53935 0%, transparent 60%)' }} />
      <div style={{ position: 'absolute', top: '2rem', left: '2rem', width: '1px', height: '3rem', background: '#27272a' }} />
      <div style={{ position: 'absolute', top: '2rem', left: '2rem', width: '3rem', height: '1px', background: '#27272a' }} />

      <div className="roadmap-content">
        <ReactMarkdown remarkPlugins={[remarkGfm]}>
          {content}
        </ReactMarkdown>
      </div>
    </motion.article>
  );
}
