import unittest

import mock
import numpy as np


import chainer
from chainer import cuda
from chainer import optimizer_hooks
from chainer import optimizers
from chainer import testing
from chainer.testing import attr


class SimpleLink(chainer.Link):

    def __init__(self, w, g):
        super(SimpleLink, self).__init__(param=w.shape)
        self.param.data = w
        self.param.grad = g


class TestOptimizerGradientNoise(unittest.TestCase):

    eta = 0.01

    def setUp(self):
        self.target = SimpleLink(
            np.arange(6, dtype=np.float32).reshape(2, 3),
            np.arange(3, -3, -1, dtype=np.float32).reshape(2, 3))

        self.noise_value = np.random.normal(
            loc=0, scale=np.sqrt(self.eta / np.power(1, 0.55)),
            size=(2, 3)).astype(np.float32)

    def check_gradient_noise(self):
        w = self.target.param.data
        g = self.target.param.grad
        xp = cuda.get_array_module(w)
        noise_value = xp.asarray(self.noise_value)

        expect = w - g - noise_value

        noise = mock.Mock(return_value=noise_value)
        opt = optimizers.SGD(lr=1)
        opt.setup(self.target)
        hook = optimizer_hooks.GradientNoise(self.eta, noise_func=noise)
        opt.add_hook(hook)
        opt.update()

        testing.assert_allclose(expect, w, rtol=0.4)
        noise.assert_called_once_with(xp, (2, 3), np.float32, hook, opt)

    def test_gradient_noise_cpu(self):
        self.check_gradient_noise()

    @attr.gpu
    def test_gradient_noise_gpu(self):
        self.target.to_gpu()
        self.check_gradient_noise()


testing.run_module(__name__, __file__)
