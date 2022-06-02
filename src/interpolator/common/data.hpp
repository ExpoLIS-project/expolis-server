#ifndef DATA_HPP
#define DATA_HPP

#include <iostream>

#include "nr.hpp"

/**
 * @brief The Data class represents the data to be interpolated.
 */
class Data
{
public:
	MatDoub longLat;
	VecDoub value;
	/**
	 * @brief Data Read data from the given stream.
	 *
	 * <p>The format of the stream is: the first line should contain an integer
	 * representing the number points; each following line should contain three
	 * floating point numbers (longitude, latitude and data value).
	 *
	 * @param is the stream to read data from.
	 */
	Data (std::istream &is);
};

#endif // DATA_HPP
