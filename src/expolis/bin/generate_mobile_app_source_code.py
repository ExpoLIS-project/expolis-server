#!/usr/bin/python3
"""
Script that generates Java source code to be used by the ExpoLIS mobile app.  The android mobile app allows a user to
see pollution versus time plots and pollution maps.  The data that is shown in these graphs is available in the ExpoLIS
sensor data server as a set of SQL functions.

Graphs are represented by instances of class `Graph`.
To create a new instance use the following template:

    NEW_GRAPH = Graph (
        variable_declaration=lambda s, d: ''''''.format (),
        variable_initialisation=lambda s, d: ''''''.format (),
        callback_function=lambda s, d, c: ''''''.format (),
        close_instruction=lambda s, d: ''''''.format (),
        callback_instruction=lambda s, d, m: ''''''.format (),
    )

"""

import argparse
import io
import os.path
from typing import TextIO
from typing import List
from typing import Dict

import data
import aggregation
import interpolation_method
from interpolation import INTERPOLATION_RESOLUTION, INTERPOLATION_STATISTIC, INTERPOLATION_PERIOD


class Graph:
    """
    Represents a graph to analyse the data collected by the Expolis sensor network.
    """
    def __init__ (
            self,
            description: str,
            uses_statistics: bool,
            variable_declaration,
            variable_initialisation,
            callback_function,
            close_instruction,
            callback_instruction,
    ):
        self.description = description
        self.uses_statistics = uses_statistics
        self.variable_declaration = variable_declaration
        self.variable_initialisation = variable_initialisation
        self.callback_function = callback_function
        self.close_instruction = close_instruction
        self.callback_instruction = callback_instruction

    def __repr__(self):
        return '{}'.format (self.description)


# <editor-fold desc="Map data">
def __graph_map_data__variable_declaration__ (s: aggregation.Statistic, d: data.Data) -> str:
    return '''
\tprivate final PreparedStatement psMapDataRaw{statistic_identifier}{data_identifier};\
'''.format (
                statistic_identifier=s.java_identifier,
                data_identifier=d.java_identifier (),
            )


def __graph_map_data__variable_initialisation__ (s: aggregation.Statistic, d: data.Data) -> str:
    return '''
\t\tthis.psMapDataRaw{statistic_java_identifier}{data_java_identifier} = \
connection.prepareStatement ("\
SELECT * \
FROM graph_map_data_raw_{statistic_sql_function}_{data_sql_identifier} (?, ?, ?)\
");\
'''.format (
                statistic_java_identifier=s.java_identifier,
                statistic_sql_function=s.sql_function,
                data_java_identifier=d.java_identifier (),
                data_sql_identifier=d.sql_identifier,
            )


def __graph_map_data__callback_function__ (s: aggregation.Statistic, d: data.Data, c: str) -> str:
    return '''
\t/**
\t * Query to compute the {statistic_description} of {data_description} for graph map data.
\t * @param fromDate the minimum date to filter the data.
\t * @param toDate the maximum date to filter the data.
\t * @param cellSize the cell size.
\t * @return a list with {{@code MapDataCell}} objects representing points in the map
\t * with {statistic_description} of {data_description}.  
\t */
\tpublic LinkedList<MapDataCell> get{statistic_identifier}{data_identifier}RawForGraphMapData (\
float cellSize, \
Timestamp fromDate, \
Timestamp toDate)
\t{{
\t\ttry {{
\t\t\tthis.psMapDataRaw{statistic_identifier}{data_identifier}.setFloat (1, cellSize);
\t\t\tthis.psMapDataRaw{statistic_identifier}{data_identifier}.setTimestamp (2, fromDate);
\t\t\tthis.psMapDataRaw{statistic_identifier}{data_identifier}.setTimestamp (3, toDate);
\t\t\treturn {class_name}.getMapDataCells (this.psMapDataRaw{statistic_identifier}{data_identifier});
\t\t}}
\t\tcatch (SQLException ex) {{
\t\t\tthrow new Error (ex);
\t\t}}
\t}}'''.format (
            statistic_description=s.description,
            data_description=d.description_en,
            statistic_identifier=s.java_identifier,
            data_identifier=d.java_identifier (),
            class_name=c,
        )


def __graph_map_data__close_instruction__ (s: aggregation.Statistic, d: data.Data) -> str:
    return '''
\t\tthis.psMapDataRaw{statistic_identifier}{data_identifier}.close ();\
'''.format (
            statistic_identifier=s.java_identifier,
            data_identifier=d.java_identifier (),
        )


def __graph_map_data__callback_instruction__ (s: aggregation.Statistic, d: data.Data, m: str) -> str:
    return '''\
get{statistic_identifier}{data_identifier}RawForGraphMapData (\
{view_model}.cellSizeInRadians, \
new Timestamp ({view_model}.fromDate), \
new Timestamp ({view_model}.toDate))'''.format (
        statistic_identifier=s.java_identifier,
        data_identifier=d.java_identifier (),
        view_model=m,
    )


GRAPH_MAP_DATA = Graph (
    description='raw data map',
    uses_statistics=True,
    variable_declaration=__graph_map_data__variable_declaration__,
    variable_initialisation=__graph_map_data__variable_initialisation__,
    callback_function=__graph_map_data__callback_function__,
    close_instruction=__graph_map_data__close_instruction__,
    callback_instruction=__graph_map_data__callback_instruction__,
)


# </editor-fold>
# <editor-fold desc="Cell data">
def __graph_cell_data__variable_declaration (s: aggregation.Statistic, d: data.Data) -> str:
    return '''
\tprivate final PreparedStatement psCellDataRaw{statistic_identifier}{data_identifier};\
'''.format (
            statistic_identifier=s.java_identifier,
            data_identifier=d.java_identifier (),
        )


def __graph_cell_data__variable_initialisation__ (s: aggregation.Statistic, d: data.Data) -> str:
    return '''
\t\tthis.psCellDataRaw{statistic_java_identifier}{data_java_identifier} = \
connection.prepareStatement ("\
SELECT * \
FROM graph_cell_data_raw_{statistic_sql_function}_{data_sql_identifier} (?, ?, ?, ?, ?)\
");\
'''.format (
            statistic_java_identifier=s.java_identifier,
            statistic_sql_function=s.sql_function,
            data_java_identifier=d.java_identifier (),
            data_sql_identifier=d.sql_identifier,
        )


def __graph_cell_data__callback_function__ (s: aggregation.Statistic, d: data.Data, c: str) -> str:
    return '''
\t/**
\t * Query to compute {statistic_description} of {data_description} for graph cell data versus time.
\t * @param cellLatitude the latitude of the position to be analysed.
\t * @param cellLongitude the longitude of the position to be analysed.
\t * @param cellRadius the radius of the position to be analysed.
\t * @param fromDate the minimum date to filter the data.
\t * @param toDate the maximum date to filter the data.
\t * @return a list with {{@code Value}} objects that represent plot points.
\t */
\tpublic LinkedList<ValueTime> get{statistic_identifier}{data_identifier}RawForGraphCellData (\
double cellLongitude, \
double cellLatitude, \
float cellRadius, \
Timestamp fromDate, \
Timestamp toDate)
\t{{
\t\ttry {{
\t\t\tthis.psCellDataRaw{statistic_identifier}{data_identifier}.setDouble (1, cellLongitude);
\t\t\tthis.psCellDataRaw{statistic_identifier}{data_identifier}.setDouble (2, cellLatitude);
\t\t\tthis.psCellDataRaw{statistic_identifier}{data_identifier}.setFloat (3, cellRadius);
\t\t\tthis.psCellDataRaw{statistic_identifier}{data_identifier}.setTimestamp (4, fromDate);
\t\t\tthis.psCellDataRaw{statistic_identifier}{data_identifier}.setTimestamp (5, toDate);
\t\t\treturn {class_name}.getValueTimes (this.psCellDataRaw{statistic_identifier}{data_identifier});
\t\t}}
\t\tcatch (SQLException ex) {{
\t\t\tthrow new Error (ex);
\t\t}}
\t}}'''.format (
        statistic_description=s.description,
        data_description=d.description_en,
        statistic_identifier=s.java_identifier,
        data_identifier=d.java_identifier (),
        class_name=c,
    )


def __graph_cell_data__close_instruction (s: aggregation.Statistic, d: data.Data) -> str:
    return '''
\t\tthis.psMapDataRaw{statistic_identifier}{data_identifier}.close ();\
'''.format (
            statistic_identifier=s.java_identifier,
            data_identifier=d.java_identifier (),
        )


def __graph_cell_data__callback_instruction__ (s: aggregation.Statistic, d: data.Data, m: str) -> str:
    return '''\
get{statistic_identifier}{data_identifier}RawForGraphCellData (\
{view_model}.locationLongitude, \
{view_model}.locationLatitude, \
{view_model}.cellRadius, \
new Timestamp ({view_model}.fromDate), \
new Timestamp ({view_model}.toDate))\
'''.format (
            statistic_identifier=s.java_identifier,
            data_identifier=d.java_identifier (),
            view_model=m,
        )


GRAPH_CELL_DATA = Graph (
            description='cell data chart',
            uses_statistics=True,
            variable_declaration=__graph_cell_data__variable_declaration,
            variable_initialisation=__graph_cell_data__variable_initialisation__,
            callback_function=__graph_cell_data__callback_function__,
            close_instruction=__graph_cell_data__close_instruction,
            callback_instruction=__graph_cell_data__callback_instruction__,
        )


# </editor-fold>
# <editor-fold desc="Line data">
def __graph_line_data__variable_declaration__ (s: aggregation.Statistic, d: data.Data) -> str:
    return '''
\tprivate final PreparedStatement psLineDataRaw{statistic_identifier}{data_identifier};\
'''.format (
        statistic_identifier=s.java_identifier,
        data_identifier=d.java_identifier (),
    )


def __graph_line_data__variable_initialisation (s: aggregation.Statistic, d: data.Data) -> str:
    return '''
\t\tthis.psLineDataRaw{statistic_java_identifier}{data_java_identifier} = \
connection.prepareStatement ("\
SELECT * \
FROM graph_line_data_raw_{statistic_sql_function}_{data_sql_identifier} (?, ?, ?, ?)\
");\
'''.format (
        statistic_java_identifier=s.java_identifier,
        data_java_identifier=d.java_identifier (),
        statistic_sql_function=s.sql_function,
        data_sql_identifier=d.sql_identifier
    )


def __graph_line_data__callback_function (s: aggregation.Statistic, d: data.Data, c: str) -> str:
    return '''
\t/**
\t * Query to compute {statistic_description} of {data_description} for graph line data.
\t * This a map of {data_description} along the locations where a bus line passes.
\t * @param lineId the identification of the bus line.
\t * @param cellRadius the size of the graph points.
\t * @param fromDate the minimum date to filter the data.
\t * @param toDate the maximum date to filter the data.
\t * @return a list with {{@code MapDataCell}} that represent graph points.
\t */
\tpublic LinkedList<MapDataCell> get{statistic_identifier}{data_identifier}RawForGraphLineData (\
int lineId, \
float cellRadius, \
Timestamp fromDate, \
Timestamp toDate)
\t{{
\t\ttry {{
\t\t\tthis.psLineDataRaw{statistic_identifier}{data_identifier}.setInt (1, lineId);
\t\t\tthis.psLineDataRaw{statistic_identifier}{data_identifier}.setFloat (2, cellRadius);
\t\t\tthis.psLineDataRaw{statistic_identifier}{data_identifier}.setTimestamp (3, fromDate);
\t\t\tthis.psLineDataRaw{statistic_identifier}{data_identifier}.setTimestamp (4, toDate);
\t\t\treturn {class_name}.getMapDataCells (this.psLineDataRaw{statistic_identifier}{data_identifier});
\t\t}}
\t\tcatch (SQLException ex) {{
\t\t\tthrow new Error (ex);
\t\t}}
\t}}'''.format (
        statistic_description=s.description,
        data_description=d.description_en,
        statistic_identifier=s.java_identifier,
        data_identifier=d.java_identifier (),
        class_name=c,
    )


def __graph_line_data__close_instruction (s: aggregation.Statistic, d: data.Data) -> str:
    return '''
\t\tthis.psLineDataRaw{statistic_identifier}{data_identifier}.close ();\
'''.format (
        statistic_identifier=s.java_identifier,
        data_identifier=d.java_identifier (),
    )


def __graph_line_data__callback_instruction (s: aggregation.Statistic, d: data.Data, m: str) -> str:
    return '''\
get{statistic_identifier}{data_identifier}RawForGraphLineData (\
{view_model}.lineId, \
{view_model}.cellSizeInMeters, \
new Timestamp ({view_model}.fromDate), \
new Timestamp ({view_model}.toDate)\
)'''.format (
        statistic_identifier=s.java_identifier,
        data_identifier=d.java_identifier (),
        view_model=m,
    )


GRAPH_LINE_DATA = Graph (
    description='line data chart',
    uses_statistics=True,
    variable_declaration=__graph_line_data__variable_declaration__,
    variable_initialisation=__graph_line_data__variable_initialisation,
    callback_function=__graph_line_data__callback_function,
    close_instruction=__graph_line_data__close_instruction,
    callback_instruction=__graph_line_data__callback_instruction,
)


# </editor-fold>
# <editor-fold desc="Interpolated data map">
def __graph_interpolated_data_map__variable_declaration__ (d: data.Data) -> str:
    return '''
\tprivate final PreparedStatement psInterpolatedDataMap{data_identifier};\
'''.format (
        data_identifier=d.java_identifier ()
    )


def __graph_interpolated_data_map__variable_initialisation__ (m: interpolation_method.Method, d: data.Data) -> str:
    return '''
\t\tthis.psInterpolatedDataMap{data_java_identifier} = \
connection.prepareStatement ("\
SELECT * \
FROM graph_interpolated_data_map_{method_sql_identifier}_{period_sql_identifier}_{data_sql_identifier} (?, ?)\
");\
'''.format (
        data_java_identifier=d.java_identifier (),
        method_sql_identifier=m.sql_identifier,
        period_sql_identifier=INTERPOLATION_PERIOD.sql_identifier,
        data_sql_identifier=d.sql_identifier
    )


def __graph_interpolated_data_map__callback_function__ (d: data.Data, c: str) -> str:
    return '''
\t/**
\t * Query to compute interpolation of {data_description} for <i>interpolated data map</i> plot.
\t * @param fromDate the minimum date to filter the data.
\t * @param toDate the maximum date to filter the data.
\t * @return a list with {{@code MapDataCell}} that represent graph points.
\t */
\tpublic LinkedList<MapDataCell> get{data_identifier}ForInterpolatedDataMap (\
Timestamp fromDate, \
Timestamp toDate)
\t{{
\t\ttry {{
\t\t\tthis.psInterpolatedDataMap{data_identifier}.setTimestamp (1, fromDate);
\t\t\tthis.psInterpolatedDataMap{data_identifier}.setTimestamp (2, toDate);
\t\t\treturn {class_name}.getMapDataCells (this.psInterpolatedDataMap{data_identifier});
\t\t}}
\t\tcatch (SQLException ex) {{
\t\t\tthrow new Error (ex);
\t\t}}
\t}}'''.format (
        data_description=d.description_en,
        data_identifier=d.java_identifier (),
        class_name=c,
    )


def __graph_interpolated_data_map__close_instruction (d: data.Data) -> str:
    return '''
\t\tthis.psInterpolatedDataMap{data_identifier}.close ();\
'''.format (
        data_identifier=d.java_identifier ()
    )


def __graph_interpolated_data_map__callback_instruction (d: data.Data, m: str) -> str:
    return '''\
get{data_identifier}ForInterpolatedDataMap (\
new Timestamp ({view_model}.fromDate), \
new Timestamp ({view_model}.toDate)\
)'''.format (
        data_identifier=d.java_identifier (),
        view_model=m,
    )


GRAPH_INTERPOLATED_DATA_MAP = Graph (
    description='interpolated data map',
    uses_statistics=False,
    variable_declaration=__graph_interpolated_data_map__variable_declaration__,
    variable_initialisation=__graph_interpolated_data_map__variable_initialisation__,
    callback_function=__graph_interpolated_data_map__callback_function__,
    close_instruction=__graph_interpolated_data_map__close_instruction,
    callback_instruction=__graph_interpolated_data_map__callback_instruction,
)
# </editor-fold>

GRAPHS_DICT = {
    'map-data': GRAPH_MAP_DATA,
    'cell-data': GRAPH_CELL_DATA,
    'line-data': GRAPH_LINE_DATA,
    'interpolation': GRAPH_INTERPOLATED_DATA_MAP,
}  # type: Dict[str, Graph]


def __graphs_list__ () -> List[Graph]:
    return [
        GRAPH_MAP_DATA,
        GRAPH_CELL_DATA,
        GRAPH_LINE_DATA,
        GRAPH_INTERPOLATED_DATA_MAP,
    ]


def __graphs_dict__ () -> Dict[str, Graph]:
    return {
        'map-data': GRAPH_MAP_DATA,
        'cell-data': GRAPH_CELL_DATA,
        'line-data': GRAPH_LINE_DATA,
        'interpolation': GRAPH_INTERPOLATED_DATA_MAP,
    }


def generate_dao (
        output: str,
        package_name: str,
        graph_classes_package: str,
        ) -> None:
    """
    Generate a Data Access Object class file.
    * output: the filename with the generated DAO.
    * package_name: the package where the class resides.
    * graph_classes_package: if specified the package where are the classes that represent graph data.
    :return:
    """
    # output = args.output
    # package_name = args.package
    # graph_classes_package = args.graph_classes_package
    if os.path.exists (output):
        print ('File {} already exists!'.format (output))
        answer = input ('Overwrite (y/n)? ')
        if answer != 'y' and answer != 'yes':
            return None
    class_name = os.path.basename (output) [:-5]
    fd = io.open (output, 'w')
    generate_dao_prologue (fd, package_name, class_name, graph_classes_package)
    for g in __graphs_list__():
        for d in data.DATA:
            if d.mobile_app_flag:
                if g.uses_statistics:
                    for s in aggregation.STATISTICS:
                        fd.write (g.variable_declaration (s=s, d=d))
                else:
                    fd.write (g.variable_declaration (d=d))
    generate_dao_constructor (fd, class_name)
    for g in __graphs_list__():
        for d in data.DATA:
            if d.mobile_app_flag:
                if g.uses_statistics:
                    for s in aggregation.STATISTICS:
                        fd.write (g.callback_function (s=s, d=d, c=class_name))
                else:
                    fd.write (g.callback_function (d=d, c=class_name))
    generate_dao_method_close (fd)
    generate_dao_epilogue (fd)
    fd.close ()


def generate_dao_prologue (
        output: TextIO,
        package_name: str,
        class_name: str,
        graph_classes_package: str,
):
    """

    :param output:
    :param package_name:
    :param class_name:
    :param graph_classes_package:
    :return:
    """
    output.write ('''\
package {};
{}
import java.sql.Connection;
import java.sql.Timestamp;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.LinkedList;

public class {}
{{'''.format (
        package_name,
        '' if graph_classes_package is None
        else '\nimport {p}.MapDataCell;\nimport {p}.ValueTime;\n'.format (p=graph_classes_package),
        class_name
    ))


def generate_dao_constructor (
        output: TextIO,
        class_name: str,
):
    output.write ('''
\tpublic {class_name} (Connection connection)
\t  throws SQLException
\t{{'''.format (
        class_name=class_name,
    ))
    for g in __graphs_list__():
        for d in data.DATA:
            if d.mobile_app_flag:
                if g.uses_statistics:
                    for s in aggregation.STATISTICS:
                        output.write (g.variable_initialisation (s=s, d=d))
                else:
                    for m in interpolation_method.METHODS:
                        output.write (g.variable_initialisation (m=m, d=d))
    output.write ('''
\t}''')


def generate_dao_method_close (
        output: TextIO,
):
    output.write ('''
\tvoid close ()
\t  throws SQLException
\t{\n''')
    for g in __graphs_list__():
        for d in data.DATA:
            if d.mobile_app_flag:
                if g.uses_statistics:
                    for s in aggregation.STATISTICS:
                        output.write (g.close_instruction (s=s, d=d))
                else:
                    output.write (g.close_instruction (d=d))
    output.write ('\t}\n')


def generate_dao_epilogue (
        output: TextIO,
):
    output.write ('''
\tprivate static LinkedList<MapDataCell> getMapDataCells (PreparedStatement ps)
\t{
\t\tLinkedList<MapDataCell> result = new LinkedList<> ();
\t\ttry (ResultSet rs = ps.executeQuery ()) {
\t\t\twhile (rs.next ()) {
\t\t\t\tMapDataCell mdc = new MapDataCell ();
\t\t\t\tmdc.latitude = rs.getDouble ("latitude");
\t\t\t\tmdc.longitude = rs.getDouble ("longitude");
\t\t\t\tmdc.value = rs.getDouble ("value");
\t\t\t\tresult.add (mdc);
\t\t\t}
\t\t\tps.clearParameters ();
\t\t}
\t\tcatch (SQLException e) {
\t\t\te.printStackTrace (System.err);
\t\t}
\t\treturn result;
\t}
\tprivate static LinkedList<ValueTime> getValueTimes (PreparedStatement ps)
\t{
\t\tLinkedList<ValueTime> result = new LinkedList<> ();
\t\ttry (ResultSet rs = ps.executeQuery ()) {
\t\t\twhile (rs.next ()) {
\t\t\t\tValueTime vt = new ValueTime ();
\t\t\t\tvt.value = rs.getDouble ("value");
\t\t\t\tvt.date_time = rs.getTimestamp ("when_").getTime ();
\t\t\t\tresult.add (vt);
\t\t\t}
\t\t\tps.clearParameters ();
\t\t}
\t\tcatch (SQLException e) {
\t\t\te.printStackTrace (System.err);
\t\t}
\t\treturn result;
\t}
}''')


def generate_switch (
        graph: str,
        output: str,
        dao: str,
        view_model: str,
):
    if os.path.exists (output):
        print ('File {} already exists!'.format (output))
        answer = input ('Overwrite (y/n)? ')
        if answer != 'y' and answer != 'yes':
            return None
    g = __graphs_dict__() [graph]
    fd = io.open (output, 'w')
    switch_code = '''
switch ({view_model}.data) {{\
'''.format (
        view_model=view_model
    )
    for d in data.DATA:
        if d.mobile_app_flag:
            switch_code += '''
case {enum}:'''.format (
                enum=d.java_enum(),
            )
            if g.uses_statistics:
                switch_code += '''
    \tswitch ({view_model}.statistics) {{'''.format (view_model=view_model)
                for s in aggregation.STATISTICS:
                    switch_code += '''
        \tcase {enum}:
        \t\treturn {dao}.{callback};\
        '''.format (
                        enum=s.java_enum,
                        dao=dao,
                        callback=g.callback_instruction (s, d, view_model)
                    )
                switch_code += '\n\t}'
            else:
                switch_code += '''
                \t\treturn {dao}.{callback};\
                '''.format (
                    dao=dao,
                    callback=g.callback_instruction (d, view_model)
                )
    switch_code += '\n}'
    fd.write (switch_code)
    fd.close ()


class Args:
    def __init__(self):
        parser = argparse.ArgumentParser (
            description='Generates java source code to access the ExpoLIS sensor data database.'
        )
        # <editor-fold desc="DAO arguments">
        parser.add_argument (
            '--graphs-sql-dao',
            type=str,
            metavar='FILENAME',
            default='GraphsSqlDao.java',
            help='Name of the java file with the class that provides functionality to access data for the graphs'
        )
        parser.add_argument (
            '-p',
            '--package',
            type=str,
            required=True,
            help='the name of the package where the generated java DAO class resides.',
        )
        parser.add_argument (
            '--graph-classes-package',
            type=str,
            default=None,
            metavar='IDENTIFIER',
            help='the package where the classes that represent graph data are stored. If not specified it assumed they '
                 'belong to the generated java class package.',
        )
        # </editor-fold>
        # <editor-fold desc="switch arguments">
        for key in GRAPHS_DICT:
            g = GRAPHS_DICT [key]
            parser.add_argument (
                '--switch-' + key,
                type=str,
                metavar='FILENAME',
                default='switch_' + key.replace ('-', '_') + '.java',
                help='Name of the java file with the switch to call data for ' + g.description,
            )
        parser.add_argument (
            '--view-model',
            type=str,
            default='this',
            metavar='EXPRESSION',
            help='a java expression that represents the view model with graph properties.',
        )
        parser.add_argument (
            '--dao',
            type=str,
            default='dao',
            metavar='EXPRESSION',
            help='a java expression that represents the DAO object.'
        )
        # </editor-fold>
        args = parser.parse_args ()
        self.graphs_sql_dao = args.graphs_sql_dao                # type: str
        self.package = args.package                              # type: str
        self.graph_classes_package = args.graph_classes_package  # type: str
        self.switch_map_data = args.switch_map_data              # type: str
        self.switch_cell_data = args.switch_cell_data            # type: str
        self.switch_line_data = args.switch_line_data            # type: str
        self.switch_interpolation = args.switch_interpolation    # type: str
        self.view_model = args.view_model                        # type: str
        self.dao = args.dao                                      # type: str


def main ():
    args = Args ()
    data.load_data ()
    generate_dao (
        output=args.graphs_sql_dao,
        package_name=args.package,
        graph_classes_package=args.graph_classes_package,
    )
    for key in GRAPHS_DICT:
        generate_switch(
            graph=key,
            output=args.__getattribute__ ('switch_' + key.replace ('-', '_')),
            view_model=args.view_model,
            dao=args.dao
        )


if __name__ == '__main__':
    main ()
