<!DOCTYPE html>
<html lang="pt">
    <head>
        <meta charset="UTF-8">
        <title>Cancelamento de Subscrição</title>
        <link rel="stylesheet" type="text/css" href="expolis.css">
    </head>
    <body>
<?php
if (filter_has_var (INPUT_POST, "email") && filter_has_var (INPUT_POST, "salt") && count ($_POST) == 2) {
    $email = filter_input (INPUT_POST, "email");
    $salt = filter_input (INPUT_POST, "salt");
    // Connecting, selecting database
    $db_connection = pg_connect ("port=10101 dbname=sensor_data user=expolis");
    if (!$db_connection) {
        echo "<p>Não foi possível estabelecer ligação à base de dados.  Tente mais tarde.</p>";
    }
    else {
        $safe_email = htmlspecialchars ($email);
        $result = pg_query_params (
                $db_connection,
                "SELECT COUNT (*) FROM subscriptions WHERE email = $1 AND salt = $2",
                [$email, $salt]);
        $line = pg_fetch_row ($result);
        if ($line [0] == 1) {
            $assoc_array = array (
                "email" => $email,
            );
            $result = pg_delete ($connection, "subscriptions", $assoc_array);
            if ($result) {
                echo "<p>Subscrição cancelada.</p>";
            }
            else {
                echo "<p>Ocorreu um problema ao cancelar a subscrição.  Tente mais tarde</p>";
            }
        }
        else {
            echo "<p>Endereço de correio electrónico inválido ou não existente, ou senha inválida.</p>";
        }
        // Closing connection
        pg_close ($db_connection);
    }
}
else {
    echo "<p>Pedido inválido!</p>";
}
?>
    </body>
</html>
