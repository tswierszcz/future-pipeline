import java.sql.*;

public class UserController {
    public ResultSet getUser(Connection connection, String userId) throws Exception {
        String query = "SELECT * FROM users WHERE id = ?";
        PreparedStatement pstmt = connection.prepareStatement(query);
        pstmt.setString(1, userId);
        return pstmt.executeQuery();
    }
}