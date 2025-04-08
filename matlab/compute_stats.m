function stats = compute_stats(G, util_par)
interval = 5;

under_util = G.util<=util_par; % true when under-utilized

% Find where the job ID changes, this will give the index for the last
% measurement for that job
% Next, get the indices for these job endpoints and add in the end of
% the final job and the "end" of the zeroth job so our index math works
bounds = ~strcmp(G.job(1:end-1),G.job(2:end));
bounds = find(bounds);
bounds = [0; bounds; height(G)];

% Set up the table that holds the GPU usage stats
var_names = ["idle_start", "idle_end", "idle_mid", "comp_tot", "comp_active", "comp_time", "comp_frac", "comp_std"];
var_types = ["double", "double", "double", "double", "double", "double", "double", "double"];
sz = [length(bounds)-1, length(var_names)];
stats = table('Size',sz,'VariableTypes',var_types,'VariableNames',var_names);

for i = 1:length(bounds)-1
    bnd_1 = bounds(i)+1;
    bnd_2 = bounds(i+1);
    % If the GPU is always under utilized, we won't be able to find a
    % start to the computation. Instead set the comp start/end equal to
    % the bounds of the whole job
    % By convention we set all idle values to 0
    if all(under_util(bnd_1:bnd_2)) 
        idle_start = 0; idle_end = 0; idle_mid = 0;
        comp_start = bnd_1;
        comp_end = bnd_2;
    else
        util_change = diff(under_util(bnd_1:bnd_2));
        
        % Find when the under_util first/last changes from 0 to 1 or 1 to 0
        % An idle start/end starts/ends with under_util=1
        % If our period actually isn't idle, then the computed value will be 0
        idle_start = under_util(bnd_1) * find(util_change ,1 ,'first') * interval;
        idle_end = under_util(bnd_2) * interval *...
            (bnd_2 - bnd_1 + 1 - find(util_change ,1 ,'last'));
        % If the job is never under-utilized, find(util_change) will be empty
        if isempty(idle_start); idle_start=0; end
        if isempty(idle_end); idle_end=0; end
        
        % Find the start and end of the computation by looking for when
        % we are first/last not under-utilizing the GPU
        % Remember that we need to add these offsets to the whole job
        % start bound
        comp_start = find(~under_util(bnd_1:bnd_2), 1, 'first') + bnd_1 - 1;
        comp_end = find(~under_util(bnd_1:bnd_2), 1, 'last') + bnd_1 - 1;
        idle_mid = sum(under_util(comp_start:comp_end)) * interval;
    end
    tot_time = (bnd_2 - bnd_1 + 1) * interval;
    comp_time = (comp_end - comp_start + 1) * interval;
    comp_tot = sum(G.util(comp_start:comp_end))/100 * interval;
    comp_active = (G.util(comp_start:comp_end)' * ~under_util(comp_start:comp_end))/100 * interval;
    comp_frac = comp_tot/comp_time;
    comp_std = std(G.util(comp_start:comp_end))/100;
    stats(i,:) = {idle_start, idle_end, idle_mid, comp_tot, comp_active, comp_time, comp_frac, comp_std};
end
% Generate job names including task IDs to match the format of the
% accounting file
% We also include GPU index so that we can disambiguate when a job uses
% multiple GPUs. We have stats on a per job per GPU basis.
[~,~,bus] = unique(G.bus(bounds(1:end-1)+1));
job = split(G.job(bounds(1:end-1)+1),'.');
job(strcmp(job(:,2),'undefined'),2)={'0'};
rundate = G.rundate(bounds(1:end-1)+1); % starting rundate for each job; we need this to distinguish between identical jobids that occured in past years
job = strcat(job(:,1),'.',job(:,2),'.',rundate);

stats = [table(job,bus), stats];
end