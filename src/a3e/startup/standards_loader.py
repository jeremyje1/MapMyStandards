"""
Standards loader startup module.
Ensures standards are loaded from corpus on application startup.
"""
import logging
from pathlib import Path
from ..services.standards_graph import standards_graph

logger = logging.getLogger(__name__)

def ensure_standards_loaded():
    """Ensure standards are loaded from corpus on startup"""
    try:
        # Check if standards are already loaded
        stats = standards_graph.get_graph_stats()
        
        if stats.get('total_nodes', 0) < 10:
            logger.info("Standards graph appears empty, loading from corpus...")
            
            # Try to load from the data/standards directory
            repo_root = Path(__file__).resolve().parents[3]
            standards_dir = repo_root / "data" / "standards"
            
            if standards_dir.exists():
                result = standards_graph.reload_from_corpus(
                    corpus_dir=str(standards_dir),
                    fallback_to_seed=True
                )
                logger.info(f"Loaded standards: {result}")
            else:
                logger.warning(f"Standards directory not found at {standards_dir}")
                logger.info("Using seed data fallback")
        else:
            logger.info(f"Standards already loaded: {stats}")
            
    except Exception as e:
        logger.error(f"Error loading standards on startup: {e}")
        logger.info("Continuing with seed data")

# Run on import
ensure_standards_loaded()
