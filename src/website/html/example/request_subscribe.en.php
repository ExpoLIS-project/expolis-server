<!DOCTYPE html>
<html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>ExpoLIS Subscription</title>
        <link rel="stylesheet" type="text/css" href="expolis.css">
    </head>
    <body>
<?php
$email = filter_input (INPUT_POST, "email", FILTER_VALIDATE_EMAIL);
if ($email === FALSE) {
    echo "<p>Invalid email!</p>";
}
else {
    $db_connection = pg_connect ("dbname=sensor_data user=expolis_admin");
    if ($db_connection === FALSE) {
        echo "<p>Could not connect to the database.  Please try again later.</p>";
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
            $data_sql = array (
                "co" => TRUE,
                "no" => TRUE,
                "pm1f" => TRUE,
                "pm25f" => TRUE,
                "pm10f" => TRUE,
                "temperature" => TRUE,
                "pressure" => TRUE,
                "humidity" => TRUE,
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
                    echo "<p>You are subscribed to the ExpoLIS data. Periodic emails will be sent to " . $safe_email . " when new data arrives.</p>";
                    echo "<p>To unsubscribe use the following link:<br>";
                    $url = "127.0.0.1/unsubscribe.php?email=" . $safe_email . "&salt=" . htmlspecialchars ($salt);
                    echo "<a href='" . $url . "'>" . $url . "</a></p>";
                }
                else {
                    echo "<p>There was a problem inserting the data...</p>";
                }
            }
            else {
                echo "<p>You have to specify a period!</p>";
            }
        }
        else {
            echo "<p>The email " . $safe_email . " is already associated to a subscription.  Please use the provided link to cancel the last subscription.</p>";
        }
        pg_close ($db_connection);
    }
}
?>
    </body>
</html>
