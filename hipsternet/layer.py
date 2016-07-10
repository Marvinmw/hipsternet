import numpy as np
import hipsternet.utils as util
import hipsternet.constant as c
import hipsternet.regularization as reg


def softmax(x):
    e_x = np.exp((x.T - np.max(x, axis=1)).T)
    return (e_x.T / e_x.sum(axis=1)).T


def fc_forward(l_in, W, b):
    return l_in @ W + b


def fc_backward(dinput, h, W, input_layer=False, lam=1e-3):
    dW = h.T @ dinput
    dW += reg.dl2_reg(W, lam)
    db = np.sum(dinput, axis=0)

    dh = None

    if not input_layer:
        dh = dinput @ W.T

    return dh, dW, db


def relu_forward(h):
    return np.maximum(h, 0)


def relu_backward(dh, h):
    out = dh.copy()
    out[h <= 0] = 0
    return out


def lrelu_forward(h, a=1e-3):
    return (h < 0) * a * h + (h >= 0) * h


def lrelu_backward(dh, h, a=1e-3):
    out = dh.copy()
    out[h < 0] *= a
    return out


def sigmoid_forward(h):
    return 1. / np.log(1 + np.exp(-h))


def sigmoid_backward(dh, cache=None):
    return sigmoid_forward(dh) * (1 - sigmoid_forward(dh))


def tanh_forward(h):
    return np.tanh(h)


def tanh_backward(dh, cache=None):
    return 1 - np.tanh(dh)**2


def dropout_forward(h, p_dropout):
    u = np.random.binomial(1, p_dropout, size=h.shape) / p_dropout
    return h * u, u


def dropout_backward(dh, dropout_mask):
    return dh * dropout_mask


def bn_forward(X, gamma, beta, cache, momentum=.9, train=True):
    running_mean, running_var = cache

    if train:
        mu = np.mean(X, axis=0)
        var = np.var(X, axis=0)

        X_norm = (X - mu) / np.sqrt(var + c.eps)
        out = gamma * X_norm + beta

        cache = (X, X_norm, mu, var, gamma, beta)

        running_mean = util.exp_running_avg(running_mean, mu, momentum)
        running_var = util.exp_running_avg(running_var, var, momentum)
    else:
        X_norm = (X - running_mean) / np.sqrt(running_var + c.eps)
        out = gamma * X_norm + beta
        cache = None

    return out, cache, running_mean, running_var


def bn_backward(dout, cache):
    X, X_norm, mu, var, gamma, beta = cache

    N, D = X.shape

    X_mu = X - mu
    std_inv = 1. / np.sqrt(var + c.eps)

    dX_norm = dout * gamma
    dvar = np.sum(dX_norm * X_mu, axis=0) * -.5 * std_inv**3
    dmu = np.sum(dX_norm * -std_inv, axis=0) + dvar * np.mean(-2. * X_mu, axis=0)

    dX = (dX_norm * std_inv) + (dvar * 2 * X_mu / N) + (dmu / N)
    dgamma = np.sum(dout * X_norm, axis=0)
    dbeta = np.sum(dout, axis=0)

    return dX, dgamma, dbeta
