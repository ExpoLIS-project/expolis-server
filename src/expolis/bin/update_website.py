#!/usr/bin/env python3

import data


# noinspection SpellCheckingInspection
def main ():
    data.load_data ()
    write_init_en_html ()
    write_init_pt_html ()
    write_request_search_php(
        language='en',
        title='Search Result',
        no_connection_database='<p>Could not establish a connection to the database server. Please try again later.</p>',
        csv_header='"timestamp", "node_id", "longitude", "latitude", "gps error"',
        no_results='<p>Your search did not produced any result!',
        download_link='<p>Your search is ready to be {a_tag_open}downloaded{a_tag_close}.</p>',
        link_valid='<p>This link is valid for <em>24 hours</em>.</p>',
    )
    write_request_search_php (
        language='pt',
        title='Resultado da Pesquisa',
        csv_header='"tempo", "id_nó", "longitude", "latitude", "erro_GPS"',
        no_connection_database='<p>Não foi possível estabelecer ligação à base de dados.  Tente mais tarde.</p>',
        no_results='<p>A sua pesquisa não devolveu resultados!</p>',
        download_link='<p>A sua pesquisa está pronta para ser {a_tag_open}descarregada{a_tag_close}.</p>',
        link_valid='<p>Esta ligação é válida durante <em>24 horas</em>.</p>',
    )
    write_request_subscribe_php (
        language='en',
        title='ExpoLIS Subscription',
        invalid_email='<p>Invalid email!</p>',
        no_connection_database='<p>Could not connect to the database.  Please try again later.</p>',
        subscription_successful='''\
<p>You are subscribed to the ExpoLIS data. Periodic emails will be sent to " . $safe_email ." when new data arrives.</p>\
<p>To unsubscribe use the following link:<br>\
<a href='" . $url . "'>" . $url . "</a></p>''',
        database_insert_problem='<p>There was a problem inserting the data...</p>',
        no_subscription_period='<p>You have to specify a period!</p>',
        email_already_exists='''
<p>The email " . $safe_email . " is already associated to a subscription.<br>
  Please use the provided link to cancel the last subscription.</p>''',
    )
    write_request_subscribe_php (
        language='pt',
        title='Subscrição ExpoLIS',
        invalid_email='<p>Endereço de correio electrónico inválido!</p>',
        no_connection_database='<p>Não foi possível estabelecer uma ligação à base de dados.  Por favor tente mais tarde.</p>',
        subscription_successful='''\
<p>Você está subscrito aos dados do ExpoLIS. \
Vão ser enviados mensagens periodicamente para o endereço " . $safe_email . " quando houver novos dados.</p>\
<p>Para cancelar a subscrição, utilize a seguinte ligação:<br>\
<a href='" . $url . "'>" . $url . "</a></p>''',
        database_insert_problem='<p>Houve um problema a criar a subscrição.  Por favor, tente mais tarde.</p>',
        no_subscription_period='<p>Tem que especificar um período!</p>',
        email_already_exists='<p>O endereço " . $safe_email . " já está associado a uma subscrição.  Para efectuar uma nova subscrição é necessário cancelar a prévia.  Utilize a ligação que foi fornecida.</p>',
    )


# noinspection SpellCheckingInspection
def write_init_en_html ():
    with open ('/var/www/html/index.en.html', 'w') as fd:
        fd.write ('''<!DOCTYPE html>
<html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>ExpoLIS Server</title>
        <link rel="stylesheet" type="text/css" href="expolis.css">
        <script language="JavaScript">
            function toggle_data(p) {
                var s = document.getElementById(p + 'all').checked;
                for (f of [''')
        first = True
        for a_data in data.DATA:
            if not a_data.subscribe_flag:
                continue
            fd.write ("{}'{}'".format (
                '' if first else ', ',
                a_data.sql_identifier,
            ))
            first = False
        fd.write (''']) {
                    document.getElementById(p + f).disabled = s;
                }
            }
            function is_datetime_local_supported () {
                var input = document.createElement('input');
                var value = 'a';
                input.setAttribute('type', 'datetime-local');
                input.setAttribute('value', value);
                return (input.value !== value);
            };
            function check_browser_datetime () {
                if (is_datetime_local_supported ()) {
                    for (i of ['date-start-split', 'date-end-split']) {
                        document.getElementById (i).style.display = 'none';
                    }
                }
                else {
                    for (i of ['date-start', 'date-end']) {
                        document.getElementById (i).style.display = 'none';
                    }
                }
            }
            function validate_date (p) {
                var y = document.getElementById (p + 'year').value;
                var M = document.getElementById (p + 'month').value;
                var d = document.getElementById (p + 'day').value;
                var h = document.getElementById (p + 'hour').value;
                var m = document.getElementById (p + 'minute').value;
                if (y == '' && M == '' && d == '' && h == '' && m == '')
                    return true;
                if (y != '' && M != '' && d != '' && (h != '' || (h == '' && m == ''))) {
                    y = parseInt (y);
                    M = parseInt (M) - 1;
                    d = parseInt (d);
                    var t = new Date (y, M, d, 0, 0, 0);
                    var ok = t.getFullYear () == y && t.getMonth () == M && t.getDate () == d;
                    if (!ok)
                        alert ("Invalid date!");
                    return ok;
                }
                alert ('If you fill the starting or end date, then you need to specify the year, month and day. You can optionally fill the hour and minutes.');
                return false;
            }
            function validate_form () {
                var e = document.getElementById ('date-start');
                return !(e.style.display == 'none' && (!validate_date ('date-start-') || !validate_date ('date-end-')));
            }
        </script>
    </head>
    <body onload="check_browser_datetime();">
        <p>Welcome to the ExpoLIS server.</p>
        <p>Fill the given form to perform a search on the data collected by the ExpoLIS sensor network, or to subscribe to receive notifications when new data is collected.</p>
        <form>
            <fieldset>
                <legend>What to you want?</legend>
                <label><input type="radio" name="request_type" onclick="document.getElementById('search').style.display = 'block';document.getElementById('subscribe').style.display = 'none'">Search</label>
                <label><input type="radio" name="request_type" onclick="document.getElementById('search').style.display = 'none';document.getElementById('subscribe').style.display = 'block'">Subscribe</label>
            </fieldset>
        </form>
        <form action="request_search.en.php" method="post" id="search" hidden onsubmit="return validate_form()">
            <fieldset>
                <legend>Data</legend>
                <div><label><input type=checkbox name=data_all id="search_all" onclick="toggle_data('search_');">all</label></div>''')
        for a_data in data.DATA:
            if a_data.subscribe_flag:
                fd.write ('''
                <div><label><input type=checkbox name=data_{sql_identifier} id="search_{sql_identifier}">{description_en}</label></div>'''.format (
                    sql_identifier=a_data.sql_identifier,
                    description_en=a_data.description_en,
                ))
        fd.write ('''
            </fieldset>
            <div>
                <label>
                    From date:
                    <input type=datetime-local step="3600" name="date-start" id="date-start">
                </label>
            </div>
            <div id="date-start-split">
                <input type=number name="date-start-year" size="1" min="2000" max="2050" placeholder="YYYY" id="date-start-year"> /
                <input type=number name="date-start-month" size="1" min="1" max="12" placeholder="MMM" id="date-start-month"> /
                <input type=number name="date-start-day" size="1" min="1" max="31" placeholder="DD" id="date-start-day">
                &nbsp;
                &nbsp;
                <input type=number name="date-start-hour" size="1" min="0" max="23" placeholder="HH" id="date-start-hour"> :
                <input type=number name="date-start-minute" size="1" min="0" max="59" placeholder="MM" id="date-start-minute">
            </div>
            <div>
                <label>
                    To date:
                    <input type=datetime-local step="3600" name="date-end" id="date-end">
                </label>
            </div>
            <div id="date-end-split">
                <input type=number name="date-end-year" size="1" min="2000" max="2050" placeholder="YYYY" id="date-end-year"> /
                <input type=number name="date-end-month" size="1" min="1" max="12" placeholder="MMM" id="date-end-month"> /
                <input type=number name="date-end-day" size="1" min="1" max="31" placeholder="DD" id="date-end-day">
                &nbsp;
                &nbsp;
                <input type=number name="date-end-hour" size="1" min="0" max="23" placeholder="HH" id="date-end-hour"> :
                <input type=number name="date-end-minute" size="1" min="0" max="59" placeholder="MM" id="date-end-minute">
            </div>
            <div><button>Submit</button></div>
        </form>
        <form action="request_subscribe.en.php" method="post" id="subscribe" hidden>
            <div><label>Email: <input type=email required name="email"></label></div>
            <fieldset>
                <legend>Periodicity</legend>
                <div><label><input type="radio" name="period" value="daily" checked>Daily</label></div>
                <div><label><input type="radio" name="period" value="hourly">Hourly</label></div>
            </fieldset>
            <fieldset>
                <legend>Data</legend>
                <div><label><input type=checkbox name=data_all id="subscribe_all" onclick="toggle_data('subscribe_');">all</label></div>''')
        for a_data in data.DATA:
            if a_data.subscribe_flag:
                fd.write ('''
                <div><label><input type=checkbox name=data_{sql_identifier} id="subscribe_{sql_identifier}">{description_en}</label></div>'''.format (
                    sql_identifier=a_data.sql_identifier,
                    description_en=a_data.description_en,
                ))
        fd.write ('''
            </fieldset>
            <div><button>Submit</button></div>
        </form>
    </body>
</html>
''')


# noinspection SpellCheckingInspection
def write_init_pt_html ():
    with open ('/var/www/html/index.en.html', 'w') as fd:
        fd.write ('''<!DOCTYPE html>
    <html lang="en">
        <head>
            <meta charset="UTF-8">
            <title>ExpoLIS Server</title>
            <link rel="stylesheet" type="text/css" href="expolis.css">
            <script language="JavaScript">
                function toggle_data(p) {
                    var s = document.getElementById(p + 'all').checked;
                    for (f of [''')
        first = True
        for a_data in data.DATA:
            if not a_data.subscribe_flag:
                continue
            fd.write ("{}'{}'".format (
                '' if first else ', ',
                a_data.sql_identifier,
            ))
            first = False
        fd.write (''']) {
                        document.getElementById(p + f).disabled = s;
                    }
                }
                function is_datetime_local_supported () {
                    var input = document.createElement('input');
                    var value = 'a';
                    input.setAttribute('type', 'datetime-local');
                    input.setAttribute('value', value);
                    return (input.value !== value);
                };
                function check_browser_datetime () {
                    if (is_datetime_local_supported ()) {
                        for (i of ['date-start-split', 'date-end-split']) {
                            document.getElementById (i).style.display = 'none';
                        }
                    }
                    else {
                        for (i of ['date-start', 'date-end']) {
                            document.getElementById (i).style.display = 'none';
                        }
                    }
                }
                function validate_date (p) {
                    var y = document.getElementById (p + 'year').value;
                    var M = document.getElementById (p + 'month').value;
                    var d = document.getElementById (p + 'day').value;
                    var h = document.getElementById (p + 'hour').value;
                    var m = document.getElementById (p + 'minute').value;
                    if (y == '' && M == '' && d == '' && h == '' && m == '')
                        return true;
                    if (y != '' && M != '' && d != '' && (h != '' || (h == '' && m == ''))) {
                        y = parseInt (y);
                        M = parseInt (M) - 1;
                        d = parseInt (d);
                        var t = new Date (y, M, d, 0, 0, 0);
                        var ok = t.getFullYear () == y && t.getMonth () == M && t.getDate () == d;
                        if (!ok)
                            alert ('Data inválida!');
                        return ok;
                    }
                    alert ('Se especificar as datas de início ou de fim, deve preencher pelo menos o ano, mês e dia. Pode preencher adicionalmente a hora, ou a hora mais os minutos.');
                    return false;
                }
                function validate_form () {
                    var e = document.getElementById ('date-start');
                    return !(e.style.display == 'none' && (!validate_date ('date-start-') || !validate_date ('date-end-')));
                }
            </script>
        </head>
        <body onload="check_browser_datetime();">
            <p>Bem-vindo ao servidor ExpoLIS.</p>
            <p>Preencha o formulário para pesquisar os dados existentes ou para subscrever o serviço de dados.
                No primeiro caso receberá um ficheiro com os dados recolhidos pela rede de sensores.
                No segundo caso receberá periodicamente uma mensagem de correio electrónico quando houver novos dados.</p>
            <form>
                <fieldset>
                    <legend>O que pretende?</legend>
                    <label><input type="radio" name="request_type" value="search" onclick="document.getElementById('search').style.display = 'block';document.getElementById('subscribe').style.display = 'none'">Pesquisa</label>
                    <label><input type="radio" name="request_type" value="subscribe" onclick="document.getElementById('search').style.display = 'none';document.getElementById('subscribe').style.display = 'block'">Subscrição</label>
                </fieldset>
            </form>
            <form action="request_search.pt.php" method="post" id="search" hidden onsubmit="return validate_form()">
                <fieldset>
                    <legend>Dados</legend>
                    <div><label><input type=checkbox name=data_all id="search_all" onclick="toggle_data('search_')">tudo</label></div>''')
        for a_data in data.DATA:
            if a_data.subscribe_flag:
                fd.write ('''
                    <div><label><input type=checkbox name=data_{sql_identifier} id="search_{sql_identifier}">{description_pt}</label></div>'''.format (
                    sql_identifier=a_data.sql_identifier,
                    description_pt=a_data.description_pt,
                ))
        fd.write ('''
                </fieldset>
                <div>
                    <label>
                        Data de início:
                        <input type=datetime-local step="3600" name="date-start" id="date-start">
                    </label>
                </div>
                <div id="date-start-split">
                    <input type=number name="date-start-year" size="1" min="2000" max="2050" placeholder="YYYY" id="date-start-year"> /
                    <input type=number name="date-start-month" size="1" min="1" max="12" placeholder="MMM" id="date-start-month"> /
                    <input type=number name="date-start-day" size="1" min="1" max="31" placeholder="DD" id="date-start-day">
                    &nbsp;
                    &nbsp;
                    <input type=number name="date-start-hour" size="1" min="0" max="23" placeholder="HH" id="date-start-hour"> :
                    <input type=number name="date-start-minute" size="1" min="0" max="59" placeholder="MM" id="date-start-minute">
                </div>
                <div>
                    <label>
                        Data de fim:
                        <input type=datetime-local step="3600" name="date-end" id="date-end">
                    </label>
                </div>
                <div id="date-end-split">
                    <input type=number name="date-end-year" size="1" min="2000" max="2050" placeholder="YYYY" id="date-end-year"> /
                    <input type=number name="date-end-month" size="1" min="1" max="12" placeholder="MMM" id="date-end-month"> /
                    <input type=number name="date-end-day" size="1" min="1" max="31" placeholder="DD" id="date-end-day">
                    &nbsp;
                    &nbsp;
                    <input type=number name="date-end-hour" size="1" min="0" max="23" placeholder="HH" id="date-end-hour"> :
                    <input type=number name="date-end-minute" size="1" min="0" max="59" placeholder="MM" id="date-end-minute">
                </div>
                <div><button>Submeter</button></div>
            </form>
            <form action="request_subscribe.pt.php" method="post" id="subscribe" hidden>
                <div><label>Endereço correio electrónico: <input type=email required name="email"></label></div>
                <fieldset>
                    <legend>Periodicidade</legend>
                    <div><label><input type="radio" name="period" value="daily" checked>Diária</label></div>
                    <div><label><input type="radio" name="period" value="hourly">Horária</label></div>
                </fieldset>
                <fieldset>
                    <legend>Data</legend>
                    <div><label><input type=checkbox name=data_all id="subscribe_all" onclick="toggle_data('subscribe_');">tudo</label></div>''')
        for a_data in data.DATA:
            if a_data.subscribe_flag:
                fd.write ('''
                    <div><label><input type=checkbox name=data_{sql_identifier} id="subscribe_{sql_identifier}">{description_pt}</label></div>'''.format (
                    sql_identifier=a_data.sql_identifier,
                    description_pt=a_data.description_pt,
                ))
        fd.write ('''
                </fieldset>
                <div><button>Submeter</button></div>
            </form>
        </body>
    </html>
''')


def write_request_search_php (
        language: str,
        title: str,
        csv_header: str,
        no_connection_database: str,
        no_results: str,
        download_link: str,
        link_valid: str,
):
    with open ('/var/www/html/request_search.{}.php'.format (language), 'w') as fd:
        fd.write ('''
<!DOCTYPE html>
<html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>''')
        fd.write (title)
        fd.write ('''</title>
        <link rel="stylesheet" type="text/css" href="expolis.css">
    </head>
<body>
<?php
// check which pollution data to select from database
$data_sql = array (
    // sql identifier used in database => header in CSV file''')
        for a_data in data.DATA:
            if a_data.subscribe_flag:
                fd.write ('\n   "{}" => "{}",'.format (
                    a_data.sql_identifier,
                    a_data.__getattribute__ ('description_{}'.format (language))
                ))
        fd.write ('''
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
$header = [''')
        fd.write (csv_header)
        fd.write ('''];
foreach ($data_sql as $key => $value) {
    $header[] = $value;
}
fputcsv ($csv_handle, $header);
// Connecting, selecting database
$db_connection = pg_connect ("dbname=sensor_data user=expolis_php");
if (!$db_connection) {
    echo "''')
        fd.write (no_connection_database)
        fd.write ('''";
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
    measurement_data_" . $key . ".value AS " . $key;
    }
    $query .= "\nFROM measurement_properties";
    foreach ($data_sql as $key => $value) {
        $query .= "
    INNER JOIN measurement_data_" . $key . " ON measurement_properties.ID = measurement_data_" . $key . ".mpID";
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
        echo "''')
        fd.write (no_results)
        fd.write ('''";
        unlink ($csv_handle);
    }
    else {
        echo "''')
        fd.write (download_link.format (
                  a_tag_open='<a href=\\"" . substr ($csv_filename, 14) . "\\">',
                  a_tag_close='</a>'))
        fd.write ('''";
        echo "''')
        fd.write (link_valid)
        fd.write ('''";
    }
}
?>
</body>
</html>
''')


def write_request_subscribe_php (
        language: str,
        title: str,
        invalid_email: str,
        no_connection_database: str,
        subscription_successful: str,
        database_insert_problem: str,
        no_subscription_period: str,
        email_already_exists: str,
) -> None:
    """
    :param language:
    :param title:
    :param invalid_email:
    :param no_connection_database:
    :param subscription_successful:
    :param database_insert_problem:
    :param no_subscription_period:
    :param email_already_exists:
    :return:
    """
    with open ('/var/www/html/request_subscribe.{}.php'.format (language), 'w') as fd:
        fd.write ('''
<!DOCTYPE html>
<html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>''')
        fd.write (title)
        fd.write ('''</title>
        <link rel="stylesheet" type="text/css" href="expolis.css">
    </head>
    <body>
<?php
$email = filter_input (INPUT_POST, "email", FILTER_VALIDATE_EMAIL);
if ($email === FALSE) {
    echo "''')
        fd.write (invalid_email)
        fd.write ('''";
}
else {
    $db_connection = pg_connect ("dbname=sensor_data user=expolis_php");
    if ($db_connection === FALSE) {
        echo "''')
        fd.write (no_connection_database)
        fd.write ('''";
    }
    else {
        $safe_email = htmlspecialchars ($email);
        $result = pg_query_params (
                $db_connection,
                "SELECT COUNT (*) FROM subscriptions WHERE email = $1",
                [$email]);
        $line = pg_fetch_row ($result);
        if ($line [0] == 0) {
            $salt = bin2hex (random_bytes (10));
            $data_sql = array (''')
        for a_data in data.DATA:
            if a_data.subscribe_flag:
                fd.write ('\n                "{}" => TRUE,'.format (
                    a_data.sql_identifier,
                ))
        fd.write ('''
            );
            if (!filter_has_var (INPUT_POST, 'data_all')) {
                foreach ($data_sql as $key => $value) {
                    if (!filter_has_var (INPUT_POST, 'data_' . $key )) {
                        $data_sql [$key] = FALSE;
                    }
                }
            }
            $data_sql ["email"] = $email;
            $data_sql ["salt"] = $salt;
            if (filter_input (INPUT_POST, 'period') == 'hourly') {
                $data_sql ["period"] = 1;
            }
            elseif (filter_input (INPUT_POST, 'period') == 'daily') {
                $data_sql ["period"] = 2;
            }
            if (array_key_exists ("period", $data_sql)) {
                $result = pg_insert ($db_connection, "subscriptions", $data_sql);
                if ($result) {
                    $url = "127.0.0.1/unsubscribe.php?email=" . $safe_email . "&salt=" . htmlspecialchars ($salt);
                    echo "''')
        fd.write (subscription_successful)
        fd.write ('''";
                }
                else {
                    echo "''')
        fd.write (database_insert_problem)
        fd.write ('''";
                }
            }
            else {
                echo "''')
        fd.write (no_subscription_period)
        fd.write ('''";
            }
        }
        else {
            echo "''')
        fd.write (email_already_exists)
        fd.write ('''";
        }
        pg_close ($db_connection);
    }
}
?>
    </body>
</html>
''')


if __name__ == '__main__':
    main ()
