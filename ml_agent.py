import patsy
import statsmodels.formula.api as smf
import scipy
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

import statsmodels.api as sm
from statsmodels.sandbox.regression.predstd import wls_prediction_std


class Column:
    AVG_MV = 0
    AVG_AGE = 1
    FULL = 2
    SHORT = 3
    TOTAL_MV = 4
    POS = 5
    GD = 6
    PTS = 7
    YEAR = 8


def linregress_CIs(xd, yd, conf=0.95):
    """Linear regression CIs FTW!"""
    alpha = 1. - conf  # significance
    n = xd.size  # data sample size
    x = np.linspace(xd.min(), xd.max(), 1000)

    # Predicted values from fitted model:
    a, b, r, p, err = scipy.stats.linregress(xd, yd)
    y = a * x + b

    sd = 1. / (n - 2.) * np.sum((yd - a * xd - b) ** 2)
    sd = np.sqrt(sd)
    sxd = np.sum((xd - xd.mean()) ** 2)  # SS total
    sx = (x - xd.mean()) ** 2  # variance of each x

    # quantile of student's t distribution for p=1-alpha/2
    q = scipy.stats.t.ppf(1. - alpha / 2, n - 2)
    # get the upper and lower CI:
    dy = q * sd * np.sqrt(1. / n + sx / sxd)
    yl = y - dy
    yu = y + dy

    return yl, yu, x


class linear_agent:

    def __init__(self, confidence=0.95, prediction_band=0.95):
        self.confidence = confidence
        self.prediction_band = prediction_band
        # === models
        self.avg_pts_linear_model = None
        self.total_pts_linear_model = None
        self.avg_pos_linear_model = None
        self.total_pos_linear_model = None

        self.avg_pts_yl = None
        self.avg_pts_yu = None
        self.avg_pts_xd = None

        self.total_pts_yl = None
        self.total_pts_yu = None
        self.total_pts_xd = None

        self.avg_pos_yl = None
        self.avg_pos_yu = None
        self.avg_pos_xd = None

        self.total_pos_yl = None
        self.total_pos_yu = None
        self.total_pos_xd = None

    def train(self, train_data):
        self.avg_pts_linear_model = smf.ols(formula="pts ~ avg_mv", data=train_data).fit()
        self.total_pts_linear_model = smf.ols(formula="pts ~ total_mv", data=train_data).fit()
        self.avg_pos_linear_model = smf.ols(formula="pos ~ avg_mv", data=train_data).fit()
        self.total_pos_linear_model = smf.ols(formula="pos ~ total_mv", data=train_data).fit()
        self.avg_pts_yl, self.avg_pts_yu, self.avg_pts_xd = linregress_CIs(train_data.avg_mv.values,
                                                                           train_data.pts.values, self.confidence)
        self.total_pts_yl, self.total_pts_yu, self.total_pts_xd = linregress_CIs(train_data.total_mv.values,
                                                                                 train_data.pts.values, self.confidence)
        self.avg_pos_yl, self.avg_pos_yu, self.avg_pos_xd = linregress_CIs(train_data.avg_mv.values,
                                                                           train_data.pos.values, self.confidence)
        self.total_pos_yl, self.total_pos_yu, self.total_pos_xd = linregress_CIs(train_data.total_mv.values,
                                                                                 train_data.pos.values, self.confidence)

    def evaluate(self, train_data, test_data, col_names):
        avg_x = pd.DataFrame({"avg_mv": np.linspace(train_data.avg_mv.min(),
                                                    train_data.avg_mv.max(),
                                                    len(train_data.avg_mv))})
        total_x = pd.DataFrame({"total_mv": np.linspace(train_data.total_mv.min(),
                                                        train_data.total_mv.max(),
                                                        len(train_data.total_mv))})

        avg_pts_prediction = self.avg_pts_linear_model.predict(test_data.avg_mv)
        total_pts_prediction = self.total_pts_linear_model.predict(test_data.total_mv)
        avg_pos_prediction = self.avg_pos_linear_model.predict(test_data.avg_mv)
        total_pos_prediction = self.total_pos_linear_model.predict(test_data.total_mv)

        avg_pts_loss = np.mean(np.square(test_data.pts - avg_pts_prediction))
        total_pts_loss = np.mean(np.square(test_data.pts - total_pts_prediction))
        avg_pos_loss = np.mean(np.square(test_data.pos - avg_pos_prediction))
        total_pos_loss = np.mean(np.square(test_data.pos - total_pos_prediction))

        fig, axes = plt.subplots(nrows=2, ncols=2)
        axes[0, 0].scatter(train_data.avg_mv, train_data.pts, label="Points", s=10, alpha=0.6)
        axes[0, 0].plot(avg_x.avg_mv, self.avg_pts_linear_model.predict(avg_x), "b-",
                        label='Linear $R^2$=%.2f' % self.avg_pts_linear_model.rsquared, alpha=0.9)
        axes[0, 0].fill_between(self.avg_pts_xd, self.avg_pts_yl, self.avg_pts_yu, alpha=0.3,
                                facecolor='blue', edgecolor='none')
        axes[0, 0].legend(loc='upper left', framealpha=0.5, prop={'size': 'small'})
        axes[0, 0].set_ylabel(col_names[Column.PTS])
        axes[0, 0].set_title("Test Set Loss:{:.2f}".format(avg_pts_loss))

        axes[0, 1].scatter(train_data.total_mv, train_data.pts, label="Points", s=10, alpha=0.6)
        axes[0, 1].plot(total_x.total_mv, self.total_pts_linear_model.predict(total_x), "b-",
                        label='Linear $R^2$=%.2f' % self.total_pts_linear_model.rsquared, alpha=0.9)
        axes[0, 1].fill_between(self.total_pts_xd, self.total_pts_yl, self.total_pts_yu, alpha=0.3,
                                facecolor='blue', edgecolor='none')
        axes[0, 1].legend(loc='upper left', framealpha=0.5, prop={'size': 'small'})
        axes[0, 1].set_title("Test Set Loss:{:.2f}".format(total_pts_loss))

        axes[1, 0].scatter(train_data.avg_mv, train_data.pos, label="Position", s=10, alpha=0.6)
        axes[1, 0].plot(avg_x.avg_mv, self.avg_pos_linear_model.predict(avg_x), "b-",
                        label='Linear $R^2$=%.2f' % self.avg_pos_linear_model.rsquared, alpha=0.9)
        axes[1, 0].fill_between(self.avg_pos_xd, self.avg_pos_yl, self.avg_pos_yu, alpha=0.3,
                                facecolor='blue', edgecolor='none')
        axes[1, 0].legend(loc='upper right', framealpha=0.5, prop={'size': 'small'})
        axes[1, 0].set_xlabel(col_names[Column.AVG_MV])
        axes[1, 0].set_ylabel(col_names[Column.POS])
        axes[1, 0].set_title("Test Set Loss:{:.2f}".format(avg_pos_loss))

        axes[1, 1].scatter(train_data.total_mv, train_data.pos, label="Position", s=10, alpha=0.6)
        axes[1, 1].plot(total_x.total_mv, self.total_pos_linear_model.predict(total_x), "b-",
                        label='Linear $R^2$=%.2f' % self.total_pos_linear_model.rsquared, alpha=0.9)
        axes[1, 1].fill_between(self.total_pos_xd, self.total_pos_yl, self.total_pos_yu, alpha=0.3,
                                facecolor='blue', edgecolor='none')
        axes[1, 1].legend(loc='upper right', framealpha=0.5, prop={'size': 'small'})
        axes[1, 1].set_xlabel(col_names[Column.TOTAL_MV])
        axes[1, 1].set_title("Test Set Loss:{:.2f}".format(total_pos_loss))

        plt.setp([a.get_xticklabels() for a in axes[0, :]], visible=False)
        plt.setp([a.get_yticklabels() for a in axes[:, 1]], visible=False)
        fig.tight_layout()
        plt.show()

    def predict(self, x):
        print(self.avg_pts_linear_model.predict(x))


if __name__ == "__main__":
    training_set_df = pd.read_pickle("./obj/train_data.pkl")
    testing_set_df = pd.read_pickle("./obj/test_data.pkl")
    numeric_big_summary_df = pd.read_pickle("./obj/numeric_big_summary_df.pkl")
    my_linear_agent = linear_agent()
    my_linear_agent.train(train_data=training_set_df)
    my_linear_agent.evaluate(train_data=training_set_df, test_data=testing_set_df, col_names=numeric_big_summary_df.columns)