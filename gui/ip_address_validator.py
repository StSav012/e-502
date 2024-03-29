# coding: utf-8

from __future__ import annotations

from typing import Tuple

from gui.pg_qt import QValidator

__all__ = ['IPAddressValidator']


class IPAddressValidator(QValidator):
    def validate(self, text: str, cursor_position: int) -> Tuple[QValidator.State, str, int]:
        if not text:
            return QValidator.State.Invalid, text, 0

        # remove leading zeroes
        while text.startswith('00'):
            text = text[1:]
            cursor_position = max(0, cursor_position - 1)
        if text.startswith('0') and not text.startswith('0.'):
            text = text[1:]
            cursor_position = max(0, cursor_position - 1)

        # remove leading zeroes in IPv4
        i: int = text.find('.0')
        while i != -1:
            if not (i + 2 == len(text) or text[i + 2] == '.'):
                if i < cursor_position + 2:
                    cursor_position -= 1
                text = text[:i + 1] + text[i + 2:]
            i = text.find('.0', i + 1)

        # insert zeroes between dots in IPv4
        i: int = text.find('..')
        while i != -1:
            if i < cursor_position + 2:
                cursor_position += 1
            text = text[:i + 1] + '0' + text[i + 1:]
            i = text.find('..')
        if text.startswith('.'):
            text = '0' + text
            cursor_position += 1

        if ':' not in text:  # assume IPv4
            # prepend IPv4 with zeroes
            while text.count('.') < 3:
                text = '0.' + text
                cursor_position += 2
            if text.count('.') > 3:
                return QValidator.State.Invalid, text, cursor_position

        # remove leading zeroes in IPv6
        i = text.find(':0')
        while i != -1:
            if i < cursor_position + 2:
                cursor_position -= 1
            text = text[:i + 1] + text[i + 2:]
            i = text.find(':0')

        import ipaddress
        new_text: str
        if set(text).issubset(set('0123456789')):
            new_text = str(ipaddress.ip_address(int(text)))
            return QValidator.State.Acceptable, new_text, len(new_text) - (len(text) - cursor_position)
        try:
            ipaddress.ip_address(text)
        except ValueError:
            if '.' in text and text.count('.') <= 3 and set(text).issubset(set('0123456789.')):
                return QValidator.State.Intermediate, text, cursor_position
            if ':' in text and set(text.casefold()).issubset(set('0123456789a''bc''def:')):
                return QValidator.State.Intermediate, text, cursor_position
            return QValidator.State.Invalid, text, cursor_position
        else:
            return QValidator.State.Acceptable, str(ipaddress.ip_address(text)), cursor_position
