class MatchData
  def values_at(*args)
    ary = self.to_a
    args.map { |n| ary[n] }
  end
end
