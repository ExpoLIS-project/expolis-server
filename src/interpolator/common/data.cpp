#include "data.hpp"

Data::Data (istream &is)
{
	double lon, lat, val;
	int n;
	is >> n;
	this->longLat.resize (n, 2);
	this->value.resize (n);
	n = 0;
	while (true) {
		is >> lon >> lat >> val;
		if (is) {
			this->longLat [n][0] = lon;
			this->longLat [n][1] = lat;
			this->value [n] = val;
			n++;
		} else
			return ;
	}
}
