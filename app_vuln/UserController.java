import java.sql.*;

public class UserController {
    public ResultSet getUser(Connection connection, String userId) throws Exception {
        String query = "SELECT * FROM users WHERE id = " + userId;
        Statement stmt = connection.createStatement();
        return stmt.executeQuery(query);
    }
}
