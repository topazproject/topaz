module Errno
  class ENOENT < SystemCallError
  end

  class EBADF < SystemCallError
  end

  class ECHILD < SystemCallError
  end

  class EACCES < SystemCallError
  end

  class EEXIST < SystemCallError
  end

  class ENOTDIR < SystemCallError
  end

  class EISDIR < SystemCallError
  end

  class EINVAL < SystemCallError
  end

  class ENOTEMPTY < SystemCallError
  end
end
