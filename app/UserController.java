import java.sql.*;

public class UserController {
    public ResultSet getUser(Connection connection, String userId) throws Exception {
        String query = "SELECT * FROM users WHERE id = ?";
        PreparedStatement stmt = connection.prepareStatement(query);
        // Bind user input as a SQL parameter.
        stmt.setString(1, userId);
        return stmt.executeQuery();
    }
}
