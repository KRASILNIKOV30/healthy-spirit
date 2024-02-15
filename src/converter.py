alpha = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'


def number_to_string(num):
    if num < 26:
        return alpha[num - 1]
    else:
        q, r = num // 26, num % 26
        if r == 0:
            if q == 1:
                return alpha[r - 1]
            else:
                return number_to_string(q - 1) + alpha[r - 1]
        else:
            return number_to_string(q) + alpha[r - 1]
