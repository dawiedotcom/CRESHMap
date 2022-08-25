#
# Regular cron jobs for the creshmap package
#
0 4	* * *	root	[ -x /usr/bin/creshmap_maintenance ] && /usr/bin/creshmap_maintenance
