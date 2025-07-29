# data_filling/tools/post_rules.py

import yaml
import os

def apply_logic_rules(df, rules_path=None):
    if not rules_path or not os.path.isfile(rules_path):
        print("ℹ️ No logic_rules_path provided or file not found. Skipping logic rules.")
        return df

    with open(rules_path, "r", encoding="utf-8") as f:
        rules = yaml.safe_load(f).get("rules", [])

    for rule in rules:
        condition = rule["if"]
        action = rule["then"]["set"]
        target_col = action["column"]
        target_val = action["value"]

        # === Handle simple condition ===
        if "column" in condition:
            col = condition["column"]
            if "equals" in condition:
                mask = df[col] == condition["equals"]
            elif "not_equals" in condition:
                mask = df[col] != condition["not_equals"]
            elif "in" in condition:
                mask = df[col].isin(condition["in"])
            else:
                continue
        elif "any_of" in condition:
            mask = False
            for cond in condition["any_of"]:
                col = cond["column"]
                if "equals" in cond:
                    mask |= (df[col] == cond["equals"])
                elif "not_equals" in cond:
                    mask |= (df[col] != cond["not_equals"])
                elif "in" in cond:
                    mask |= df[col].isin(cond["in"])
        elif "all_of" in condition:
            mask = True
            for cond in condition["all_of"]:
                col = cond["column"]
                if "equals" in cond:
                    mask &= (df[col] == cond["equals"])
                elif "not_equals" in cond:
                    mask &= (df[col] != cond["not_equals"])
                elif "in" in cond:
                    mask &= df[col].isin(cond["in"])
        else:
            continue  # unsupported condition

        df.loc[mask, target_col] = target_val

    return df
