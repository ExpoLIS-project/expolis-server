CPPFLAGS = -Icommon -Inr -Wall

build/kriging: kriging/main_kriging.o common/data.o common/log.o common/options.o
	g++ -o $@ $^ -lm -lboost_program_options

build:
	mkdir build
