#ifndef LOG_HPP
#define LOG_HPP

#include "data.hpp"
#include "options.hpp"

void log_interpolation_start (const Data &data, const Options &options, const string &method);
void log_interpolation_finished ();
void log_message (const string &message);

#endif // LOG_HPP
