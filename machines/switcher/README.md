# Switcher

The ATEM 1 M/E Production Studio 4K, driven from a page: program, preview, cut, auto, fade to black, the three auxes,
the multiview windows and the video mode, each one press. [`panel.py`](panel.py) stays joined to the switcher over its
network port (UDP 9910, [`atem.py`](atem.py)) and serves the page on port 8970. Any machine with a leg on the
switcher's network can wear it; today that is the `bounce` Pi, cabled to it directly.

The switcher's own front buttons only pick what Aux 1, 2 and 3 carry (the 1/2/3 keys choose the aux, the ten choose
the source). Its multiview is HD whatever the mode (1080i59.94 under 2160p29.97). The USB-B port is Blackmagic's
setup protocol only.
