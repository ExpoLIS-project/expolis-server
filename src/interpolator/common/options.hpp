#ifndef OPTIONS_HPP
#define OPTIONS_HPP

#include <iostream>
#include <string>

struct Options {
	std::istream *input;
	std::ostream *output;
	std::ostream *verbose;
	double min_latitude;
	double max_latitude;
	double min_longitude;
	double max_longitude;
	double grid_size;
	double beta;
	/**
	 * @brief Options Process command line options and return an object with the result.
	 * @param message Message to be shown with the help option.
	 * @param argv number of command line options.
	 * @param vm the map with the command line options.
	 */
	Options (const std::string &message, int argc, char *argv[]);
	~Options ();
};

#endif // OPTIONS_HPP
