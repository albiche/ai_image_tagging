# main.py

import yaml
from data_filling.pipelines.run_from_folder import run_pipeline_folder
from data_filling.pipelines.run_from_csv    import run_pipeline_csv
from scripts.batch_pipeline import run_pipeline_batch_all_combinations

if __name__ == "__main__":
    # Charge la configuration
    with open("config/conf.yml", "r", encoding="utf-8") as f:
        conf = yaml.safe_load(f)

    # Lance la bonne pipeline selon la source déclarée
    if "dataset_link" in conf:
        run_pipeline_csv(conf)
    else:
        run_pipeline_folder(conf)
