from layers.ingestion import ingest
from layers.processing import process
from layers.contentGeneration import generate_images

def run_pipeline():
    print("Starting pipeline execution...")
    ingest()

    print("Ingestion completed. Processing articles...")
    process()
    
    print("Processing completed. Generating images...")
    generate_images()
    

if __name__ == "__main__":
    run_pipeline()
    print("Pipeline executed successfully.")