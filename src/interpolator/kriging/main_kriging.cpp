#include <iostream>
#include <string>

#include "nr.hpp"
#include "ludcmp.hpp"
#include "krig.hpp"
#include "options.hpp"
#include "data.hpp"
#include "log.hpp"

using namespace std;

template<class T>
void writeInterpolation (Options &options, Krig<T> &krig)
{
	VecDoub longLat (2);
	longLat [1] = options.min_latitude;
	while (longLat [1] <= options.max_latitude) {
		longLat [0] = options.min_longitude;
		while (longLat [0] <= options.max_longitude) {
			(*options.output)
			      << longLat [0] << '\t'
			      << longLat [1] << '\t'
			      << krig.interp (longLat) << '\n';
			longLat [0] += options.grid_size;
		}
		longLat [1] += options.grid_size;
	}
}

int main (int argc, char *argv[])
{
	Options options ("Perform Kriging interpolation on a set of sparse geographic data.", argc, argv);
	Data data (*options.input);
	if (options.verbose)
		(*options.verbose) << "read " << data.longLat.nrows() << " data pointsx\n";
	log_interpolation_start (data, options, "kriging");
	log_message ("computing variogram");
	Powvargram vgram (data.longLat, data.value, options.beta);
	if (options.verbose)
		(*options.verbose) << "variogram computed\n";
	log_message ("running kriging algorithm");
	Krig<Powvargram> krig (data.longLat, data.value, vgram);
	if (options.verbose)
		(*options.verbose) << "kriging finished\n";
	log_message ("writing interpolation");
	writeInterpolation (options, krig);
	log_interpolation_finished ();
	return 0;
}
