#include <iostream>
#include <fstream>
#include <stdlib.h>
#include <boost/program_options.hpp>

#include "options.hpp"

using namespace std;
namespace po = boost::program_options;

Options::Options (const string &message, int argc, char *argv[])
{
	// Declare the supported options.
	po::options_description desc (message + "  Options are:");
	desc.add_options ()
	("help,h", "show this help message and exit.")
	(
	   "input",
	   po::value<string> ()
	   ->value_name ("FILENAME"),
	   "input file to read.  If not specified, read form standard input.")
	(
	   "output",
	   po::value<string> ()
	   ->value_name ("FILENAME"),
	   "name of the output file where the Kriging interpolation is written.  If not specified standard output is used.")
	(
	   "min-latitude",
	   po::value<double> (&this->min_latitude),
	   "minimum latitude of the interpolated grid")
	(
	   "min-longitude",
	   po::value<double> (&this->min_longitude),
	   "minimum longitude of the interpolated grid")
	(
	   "max-latitude",
	   po::value<double> (&this->max_latitude),
	   "minimum latitude of the interpolated grid")
	(
	   "max-longitude",
	   po::value<double> (&this->max_longitude),
	   "minimum longitude of the interpolated grid")
	(
	   "grid-cell-size",
	   po::value<double> (&this->grid_size)
	   ->default_value (0.001)
	   ->value_name ("D"),
	   "grid cell size in angles")
	(
	   "beta",
	   po::value<double> (&this->beta)
	   ->default_value (0.015)
	   ->value_name ("B"),
	   "beta parameter used in the variagram")
	(
	   "verbose,v",
	   "be verbose about the interpolation process")
	;
	po::variables_map vm;
	po::store (po::parse_command_line (argc, argv, desc), vm);
	po::notify (vm);
	if (vm.count ("help")) {
		cerr << desc << "\n";
		exit (0);
	}
	if (vm.count ("min-latitude") == 0 || vm.count ("max-latitude") == 0
	      || vm.count ("min-longitude") == 0 || vm.count ("max-longitude") == 0) {
		cerr << "Location of interpolated grid not fully specified!\n";
		cerr << desc << '\n';
		exit (1);
	}
	this->input = vm.count ("input") ? new ifstream (vm ["input"].as<string> ()) : &cin;
	this->output = vm.count ("output") ? new ofstream (vm ["output"].as<string> ()) : &cout;
	this->verbose = vm.count ("verbose") ? (vm.count ("output") ? &cout : &cerr) : NULL;
}

Options::~Options ()
{
	if (this->input != &cin) {
		((ifstream *) this->input)->close ();
		delete this->input;
	}
	if (this->output != &cout) {
		((ofstream *) this->output)->close ();
		delete this->output;
	}
}
