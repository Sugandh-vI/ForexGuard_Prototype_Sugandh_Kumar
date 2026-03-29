# main.py
import argparse
from src.utils.logger import get_logger

logger = get_logger("main")

def main():
    parser = argparse.ArgumentParser(description="ForexGuard Pipeline")
    parser.add_argument("--step", choices=["data", "features", "train", "stream", "serve"], required=True)
    parser.add_argument("--model", choices=["iforest", "lstm", "all"], default="iforest")
    args = parser.parse_args()

    if args.step == "data":
        from src.data_gen.generate_events import generate_dataset
        generate_dataset()

    elif args.step == "features":
        from src.features.feature_engineering import run_feature_pipeline
        run_feature_pipeline()

    elif args.step == "train":
        if args.model in ("iforest", "all"):
            from src.models.isolation_forest import run_isolation_forest
            run_isolation_forest()
        if args.model in ("lstm", "all"):
            from src.models.lstm_autoencoder import run_lstm_autoencoder
            run_lstm_autoencoder()

    elif args.step == "stream":
        from src.pipelines.streaming_pipeline import run_streaming_pipeline
        run_streaming_pipeline()

    elif args.step == "serve":
        import uvicorn
        import yaml
        with open("configs/config.yaml") as f:
            cfg = yaml.safe_load(f)
        uvicorn.run(
            "src.api.main:app",
            host    = cfg["api"]["host"],
            port    = cfg["api"]["port"],
            reload  = True,
        )

if __name__ == "__main__":
    main()