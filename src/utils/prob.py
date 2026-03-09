from random import choices


def prob(variants, probs):
    s = sum(probs)
    probs = [i / s for i in probs]
    return choices(variants, probs, k=1)[0]


def choose(*args):
    """

    :param args: list prob_a, val_a, prob_b, val_b, ...
    :return:
    """
    return prob(args[1::2], args[::2])
