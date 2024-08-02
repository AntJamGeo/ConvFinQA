import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

BLUE = "#6495ED"
GREEN = "#3CB371"

def plot_by_question_number(computational, operation):
    ACCURACY = "Accuracy"
    SAMPLES = "Samples"

    def to_df(lst):
        return pd.DataFrame(
            {
                ACCURACY: [v.accuracy for v in lst],
                SAMPLES: [v.total for v in lst],
            }
        )

    def bar_plot(df, measure, ax, color):
        bar_plot = sns.barplot(data=df, x=range(len(df)), y=ACCURACY, color=color, ax=ax)
        bar_plot.set_title(f"{measure} Accuracy by Question Number", pad=20)
        bar_plot.set_xlabel("Question Number")
        bar_plot.grid(True, linestyle="--", alpha=0.8)
        bars = [p for p in bar_plot.patches if p.get_width() > 0]
        for i, x in enumerate([p.get_x() + p.get_width() / 2 for p in bars]):
            y = bar_plot.get_ylim()[1]
            bar_plot.text(x, y, f"n={df[SAMPLES][i]}", ha="center", va="bottom", fontsize=10, color="black")

    c_df = to_df(computational)
    o_df = to_df(operation)

    _, axs = plt.subplots(nrows=1, ncols=2, figsize=(16, 8))

    bar_plot(c_df, "Computational", axs[0], BLUE)
    bar_plot(o_df, "Operation", axs[1], GREEN)
    plt.show()

def plot_by_question_type(computational, operation):
    OPERATION = "Operation"
    ACCURACY = "Accuracy"
    SAMPLES = "Samples"
    MEASURE = "Measure"

    df = pd.concat(
        [
            pd.DataFrame(
                {
                    OPERATION: computational.keys(),
                    ACCURACY: [v.accuracy for v in computational.values()],
                    SAMPLES: [v.total for v in computational.values()],
                    MEASURE: "Computation"
                }
            ),
            pd.DataFrame(
                {
                    OPERATION: operation.keys(),
                    ACCURACY: [v.accuracy for v in operation.values()],
                    SAMPLES: [v.total for v in operation.values()],
                    MEASURE: "Operation"
                }
            ),
        ]
    )

    _, ax = plt.subplots(1, 1, figsize=(12, 8))
    bar_plot = sns.barplot(data=df, x=OPERATION, y=ACCURACY, hue=MEASURE, palette={"Computation": BLUE, "Operation": GREEN}, ax=ax)

    ax.set_title("Comparison of Accuracy Scores by Operation", fontsize=16, pad=20)
    ax.set_xlabel(OPERATION, fontsize=14)
    ax.grid(True, linestyle='--', alpha=0.8)

    for x in ax.get_xticks():
        y = bar_plot.get_ylim()[1]
        bar_plot.text(x, y, f"n={df[SAMPLES][x].iloc[0]}", ha='center', va='bottom', fontsize=10, color='black')