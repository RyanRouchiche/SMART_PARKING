import ipaddress
import socket
from urllib.parse import urlparse

import cv2
from django.conf import settings

ALLOWED_SCHEMES = {'rtsp', 'rtsps', 'http', 'https'}


class UnsafeSource(ValueError):
    pass


def allowed_address(address):
    ip = ipaddress.ip_address(address.split('%')[0])
    if ip.version == 6 and ip.ipv4_mapped:
        ip = ip.ipv4_mapped
    if settings.CAMERA_NETWORKS:
        return any(ip in network for network in settings.CAMERA_NETWORKS)
    return not (ip.is_loopback or ip.is_link_local or ip.is_unspecified or ip.is_multicast or ip.is_reserved)


def is_url(value):
    return len(urlparse(value).scheme) > 1


def check_camera_url(value):
    url = urlparse(value)
    if url.scheme not in ALLOWED_SCHEMES or not url.hostname:
        raise UnsafeSource('Camera URL must use rtsp, rtsps, http or https')
    try:
        infos = socket.getaddrinfo(url.hostname, url.port or None)
    except (socket.gaierror, UnicodeError, ValueError):
        raise UnsafeSource('Camera host cannot be resolved')
    if not all(allowed_address(info[4][0]) for info in infos):
        raise UnsafeSource('Camera host is not allowed')


def open_source(path, *params):
    if is_url(path):
        try:
            check_camera_url(path)
        except UnsafeSource:
            return cv2.VideoCapture()
    return cv2.VideoCapture(path, cv2.CAP_ANY, *params) if params else cv2.VideoCapture(path)
