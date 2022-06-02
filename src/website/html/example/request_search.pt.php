<!DOCTYPE html>
<html lang="pt">
    <head>
        <meta charset="UTF-8">
        <title>Resultado da pesquisa</title>
        <link rel="stylesheet" type="text/css" href="expolis.css">
    </head>
<body>
<?php
// check which pollution data to select from database
$data_sql = array (
    // sql identifier used in database => header in CSV file
    "co" => "CO",
    "no" => "NO2",
    "pm1f" => "PM 1",
    "pm25f" => "PM 2.5",
    "pm10f" => "PM 10",
    "temperature" => "temperatura",
    "pressure" => "pressão",
    "humidity" => "humidade",
);
if (!filter_has_var (INPUT_POST, 'data_all')) {
    foreach ($data_sql as $key => $value) {
        if (!filter_has_var (INPUT_POST, 'data_' . $key )) {
            unset ($data_sql [$key]);
        }
    }
}
do {
    $csv_filename = "/var/www/html/dataset/dataset_search_" . bin2hex (random_bytes (20)) . ".csv";
} while (file_exists ($csv_filename));
$csv_handle = fopen ($csv_filename, "w");
// write the CSV header
$header = ["timestamp", "node_id", "longitude", "latitude", "gps error"];
foreach ($data_sql as $key => $value) {
    $header[] = $value;
}
fputcsv ($csv_handle, $header);
// Connecting, selecting database
$db_connection = pg_connect ("dbname=sensor_data user=expolis_app");
if (!$db_connection) {
    echo "<p>Não foi possível estabelecer ligação à base de dados.  Tente mais tarde.</p>";
}
else {
    // Create the SQL query
    $query = "SELECT
    measurement_properties.when_,
    measurement_properties.nodeID,
    measurement_properties.longitude,
    measurement_properties.latitude,
    measurement_properties.gps_error";
    foreach ($data_sql as $key => $value) {
        $query .= ",
    measurement_" . $key . ".value AS " . $key;
    }
    $query .= "\nFROM measurement_properties";
    foreach ($data_sql as $key => $value) {
        $query .= "
    INNER JOIN measurement_" . $key . " ON measurement_properties.ID = measurement_" . $key . ".mpID";
    }
    // function to compute date
    function compute_date ($prefix) {
        if (filter_has_var (INPUT_POST, $prefix)
                && filter_input (INPUT_POST, $prefix) != "") {
            $result = filter_input (INPUT_POST, $prefix);
        }
        else if (filter_has_var (INPUT_POST, $prefix . "-year")
                && filter_input (INPUT_POST, $prefix . "-year") != "") {
            $result =
                    filter_input (INPUT_POST, $prefix . "-year") . "-" .
                    filter_input (INPUT_POST, $prefix . "-month") . "-" .
                    filter_input (INPUT_POST, $prefix . "-day");
            if (filter_has_var (INPUT_POST, $prefix . "-hour")
                && filter_input (INPUT_POST, $prefix . "-hour") != "") {
                $result .=
                        "T" . filter_input (INPUT_POST, $prefix . "-hour") . ":";
                if (filter_has_var (INPUT_POST, $prefix . "-minute")
                    && filter_input (INPUT_POST, $prefix . "-minute") != "") {
                    $result .= filter_input (INPUT_POST, $prefix . "-minute");
                }
                else {
                    $result .= "00";
                }
            }
        }
        else {
            $result = NULL;
        }
        return $result;
    }
    $parameters = array ();
    $first = TRUE;
    $date_start = compute_date ("date-start");
    if ($date_start != NULL) {
        $first = FALSE;
        $query = $query . "\nWHERE";
        $query = $query . "\n    when_ >= CAST ($1 AS timestamp)";
        $parameters [] = $date_start;
    }
    $date_end = compute_date ("date-end");
    if ($date_end != NULL) {
        if ($first) {
            $query = $query . "\nWHERE";
            $first = FALSE;
            $query = $query . "\n    when_ <= CAST ($1 AS timestamp)";
        }
        else {
            $query = $query . " AND";
            $query = $query . "\n    when_ <= CAST ($2 AS timestamp)";
        }
        $parameters [] = $date_end;
    }
    // run the query
    $result = pg_query_params ($db_connection, $query, $parameters);
    // write the results to the CSV file
    $size = 0;
    while ($line = pg_fetch_array ($result, null, PGSQL_ASSOC)) {
        fputcsv ($csv_handle, $line);
        $size += 1;
    }
    // Free resultset
    pg_free_result ($result);
    // Closing connection
    pg_close ($db_connection);
    fclose ($csv_handle);
    if ($size == 0) {
        echo "<p>A sua pesquisa não devolveu resultados!</p>";
        unlink ($csv_handle);
    }
    else {
        echo '<p>A sua pesquisa está pronta para ser <a href="', substr ($csv_filename, 14), '">descarregada</a>.</p>';
        echo '<p>Esta ligação é válida durante <em>24 horas</em>.</p>';
    }
}
?>
</body>
</html>
