import java.sql.*;

public class UserController {
    public ResultSet getUser(Connection connection, String userId) throws Exception {
        String query = "SELECT * FROM users WHERE id = ?";
        PreparedStatement stmt = connection.prepareStatement(query);
        stmt.setString(1, userId);
        return stmt.executeQuery();
    }
}
