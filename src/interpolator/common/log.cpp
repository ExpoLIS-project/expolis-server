#include <string>
#include <time.h>

#include "log.hpp"

using namespace std;

const string LOG_FILENAME = "/tmp/expolis-interpolation.log";

static string time_as_string ();

void log_interpolation_start (const Data &data, const Options &options, const string &method)
{
	ofstream ofs (LOG_FILENAME, ios::app);
	ofs
	      << time_as_string ()
	      << " applying interpolation method " << method
	      << " on " << data.value.size() << " rows of data, to produce a grid of "
	      << options.min_latitude << "X" << options.max_latitude << " "
	      << options.min_longitude << "X" << options.max_longitude << "\n";
	ofs.close ();
}

void log_interpolation_finished ()
{
	log_message ("interpolation finished");
}

void log_message (const string &message)
{
	ofstream ofs (LOG_FILENAME, ios::app);
	ofs
	    << time_as_string ()
	    << ' '
	    << message
	    << '\n';
	ofs.close ();
}


string time_as_string ()
{
	time_t now;
	struct tm tm;
	char buffer[200];
	time (&now);
	localtime_r (&now, &tm);
	strftime (buffer, sizeof (buffer), "%Y-%m-%dT%H:%M:%S", &tm);
	return buffer;
}
