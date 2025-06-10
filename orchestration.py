from layers.ingestion import ingest
from layers.processing import process
from layers.contentGeneration import generate_images

def run_pipeline():
    ingest()
    process()
    generate_images()

if __name__ == "__main__":
    run_pipeline()
    print("Pipeline executed successfully.")