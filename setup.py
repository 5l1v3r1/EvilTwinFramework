#!/usr/bin/env python
import sys, os
sys.path.append('./core')
sys.path.append('./utils')

from textwrap import dedent
from utils.utils import FileHandler

if os.geteuid() != 0:
        print "You are not privileged enough."
        sys.exit(1)

try:
	import apt
except Exception:
	print "[-] 'python-apt' package does not exist, installing"
	os.system('apt-get install -y python-apt')
	print "[-] Retrying to import apt module"
	import apt

try:
    print "[+] Adding kali-linux repositories to /etc/apt/sources.list"
    apt_source_fhandler = FileHandler("/etc/apt/sources.list")
    apt_source_fhandler.write(dedent("""
                                    deb http://repo.kali.org/kali kali-rolling main non-free contrib
                                    deb-src http://repo.kali.org/kali kali-rolling main non-free contrib
                                    """))
except Exception as e:
    print "[-] This tool is only supported by Debian systems"
    print "[-] You should have apt package manager installed."
    sys.exit(1)


basic_dependencies = ["dnsmasq", "hostapd", "python-pyric", "python-scapy"]
complete_install = ["gnome-terminal", "mitmf", "beef-xss", "ettercap-common", "sslstrip"]

print "[+] Adding packages to install to list."
package_list = basic_dependencies

if len(sys.argv) == 2:
    if sys.argv[1] == "-c" or sys.argv[1] == "--complete":
        print "[+] Adding complete package set to install to list."
        package_list += complete_install

print "[+] Updating apt... (This may take a while)"
cache = apt.cache.Cache()
cache.update()  # apt-get update
cache.open()    # use the updated list

print "[+] Apt successfully updated, preparing to install packages"
for pkg in package_list:
    try:
        print "[+] Preparing to install '{}'".format(pkg)
        apt_pkg = cache[pkg]

        if apt_pkg.is_installed:
            print "[-] '{}' already installed, skipping...".format(pkg)
        else:
            apt_pkg.mark_install()
            cache.commit()
            print "[+] Installation of package '{}' was successful.".format(pkg)

        if pkg == "python-pyric":
            print "[+] Upgrading Pyric version."
            os.system('pip install --upgrade PyRic')

    except Exception as e:
        print e
        print "[-] Installation of package '{}' failed.".format(pkg)

apt_source_fhandler.restore_file()
